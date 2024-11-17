import json

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress
from rich.markup import escape
from rich.padding import Padding


from src.schema import ChatState, ChatMessage, Role, ChatMode, CommandOption, TaskMeta
from src.tasks import (
    load_tasks,
    save_task,
    delete_task,
    run_task,
    load_task_script,
    save_task_script,
    load_task_plan,
    save_task_plan,
)

from ..base import BaseAction
from ..shell import get_system_info

from .task_definition import get_task_definition
from .extract import extract_task_meta, extract_task_script


class TaskAction(BaseAction):
    """
    Used for managing, creating, running tasks
    """

    cmd_options = [
        CommandOption(
            template="\\task list",
            description="List all available tasks",
            prefix="\\task",
        ),
        CommandOption(
            template="\\task create <slug>",
            description="Create a new task",
            prefix="\\task",
        ),
        CommandOption(
            template="\\task delete <slug>",
            description="Delete an existing task",
            prefix="\\task",
        ),
        CommandOption(
            template="\\task update <slug>",
            description="Update an existing task",
            prefix="\\task",
        ),
        CommandOption(
            template="\\task inspect <slug>",
            description="Show details about a task",
            prefix="\\task",
        ),
        CommandOption(
            template="\\task run <slug>",
            description="Run a specific task",
            prefix="\\task",
            example="\\task run news",
        ),
    ]

    def __init__(self, console: Console, vendor, model_option: str) -> None:
        super().__init__(console)
        self.vendor = vendor
        self.model_option = model_option
        self.tasks = load_tasks()
        self.system_info = get_system_info()
        self.task_step_initialised = False

    def is_match(self, query_text: str, state: ChatState, cmd_options: list[CommandOption]) -> bool:
        matches_other_cmd = self.matches_other_cmd(query_text, state, cmd_options)
        if matches_other_cmd:
            return False
        elif state.mode.startswith(ChatMode._TaskPrefix):
            return bool(query_text)
        else:
            return query_text.startswith("\\task")

    def run(self, query_text: str, state: ChatState) -> ChatState:
        if query_text == "\\task list":
            return self.run_list_tasks(query_text, state)
        elif query_text.startswith("\\task inspect"):
            return self.run_inspect_task(query_text, state)
        elif query_text.startswith("\\task delete"):
            return self.run_delete_task(query_text, state)
        elif query_text.startswith("\\task update"):
            return self.run_start_task_edit(query_text, state)
        elif query_text.startswith("\\task create"):
            return self.run_start_task_edit(query_text, state)
        elif query_text.startswith("\\task run"):
            return self.run_task(query_text, state)
        else:
            # We're in task mode running create or update
            return self.run_task_edit(query_text, state)

    def run_task(self, query_text: str, state: ChatState) -> ChatState:
        slug = query_text.split()[-1]
        if slug not in self.tasks:
            self.con.print(f"\n[bold red]Error: Task with slug '{slug}' not found[/bold red]")
            return state

        # TODO: Gather input data somehow
        input_data = {}

        self.con.print(f"[green]Running task '{slug}'[/green]")
        output_data = run_task(slug, input_data)
        self.con.print(f"[green]Results:[/green]")
        self.con.print_json(data=output_data)

        task_results = f"Result of task {slug}:\n" + json.dumps(output_data, indent=2)
        state.messages.append(ChatMessage(role=Role.User, content=task_results))
        return state

    def run_list_tasks(self, query_text: str, state: ChatState) -> ChatState:
        if self.tasks:
            table = Table(show_header=False, box=None, padding=(0, 1))
            table.add_column("Name", style="green")
            table.add_column("Slug", style="dim")
            table.add_column("Description", style="dim", width=50, overflow="fold")
            for task in self.tasks.values():
                table.add_row(task.name, task.slug, task.description)

            self.con.print(Panel(table, title="Tasks", border_style="dim"))
        else:
            self.con.print("\n[yellow]No tasks found[/yellow]\n")

        return state

    def run_delete_task(self, query_text: str, state: ChatState) -> ChatState:
        slug = query_text.split()[-1]
        if not slug:
            self.con.print(
                f"\n[bold red]Error: You must provide a slug to delete a task[/bold red]"
            )
            return state

        # Check if any task depends on this one
        for task_slug, task in self.tasks.items():
            if slug in task.depends_on:
                self.con.print(
                    f"\n[bold red]Error: Cannot delete task '{slug}' because task '{task_slug}' depends on it[/bold red]"
                )
                return state

        delete_task(slug)
        self.con.print(f"\n[green]Task '{slug}' deleted successfully[/green]")
        self.tasks = load_tasks()
        return state

    def run_inspect_task(self, query_text: str, state: ChatState) -> ChatState:
        slug = query_text.split()[-1]
        if not slug:
            self.con.print(
                f"\n[bold red]Error: You must provide a slug for a task to inspect[/bold red]"
            )
            return state

        if slug not in self.tasks:
            self.con.print(f"\n[bold red]Error: Slug `{slug}` not found in task list[/bold red]")
            return state

        task = self.tasks[slug]
        task_json = task.model_dump_json(indent=2)

        script_text = load_task_script()
        if script_text:
            self.con.print("[green]Task script[/green]")
            self.con.print(f"```python\n{script_text}\n```\n")

        self.con.print("[green]Task definition[/green]")
        self.con.print(f"```json\n{task_json}\n```")
        return state

    def run_start_task_edit(self, query_text: str, state: ChatState) -> ChatState:
        slug = query_text.split()[-1]
        if not slug:
            self.con.print(
                f"\n[bold red]Error: You must provide a slug for your new task[/bold red]"
            )
            return state

        state.mode = ChatMode.TaskDefine
        state.task_slug = slug

        def get_task_define_step_instruction(slug: str, existing_task: TaskMeta | None):
            instruction = f"""
            You are to engage with an interactive, iterative chat with the user
            in order to define the task definition for the task with slug "{slug}". 
            Use this task slug "{slug}" don't make up your own.

            Do not print any code snippets, this is a high level discussion about what the task should achieve
            and its interface. You may print the input and output JSON schema for clarification.

            Once you are confident that you understand what you need to do, print a
            final message containing a JSON object defining the task metadata.

            The JSON object should be wrapped in a standard markdown code block (```json) so it can be extracted.

            This is step one of a multi-process workflow. Your only job in this step is to produce
            the task definition JSON. Do not attempt produce a python script - that comes later.

            Once you have a JSON in mind then print it out in every response.
            """
            if existing_task:
                task_json = existing_task.model_dump_json(indent=2)
                instruction += f"\nThis is the current definition for this task, use this as a starting point:\n{task_json}"

            return instruction

        existing_task = self.tasks.get(state.task_slug)
        other_tasks = {k: v for k, v in self.tasks.items() if k != state.task_slug}
        task_definition = get_task_definition(state.task_slug, other_tasks, self.system_info)
        task_define_step_instruction = get_task_define_step_instruction(
            state.task_slug, existing_task
        )
        state.task_thread = [
            ChatMessage(role=Role.User, content=task_definition),
            ChatMessage(role=Role.User, content=task_define_step_instruction),
        ]
        self.task_step_initialised = True
        self.con.print(f'\n[bold cyan]Task definition step for "{state.task_slug}"[/bold cyan]\n')
        intro = """
        Here you will describe your task to the assistant, who will provide you with
        a task definiton JSON. Once you're happy with the JSON you can accept it.        
        """
        panel = Panel(intro, title="Instructions", border_style="dim", padding=(0, 0))
        self.con.print(panel)

        if existing_task:
            task_json = existing_task.model_dump_json(indent=2)
            self.con.print(f"Existing task found:\n{task_json}")
            self.con.print(
                f"\nAssistant: Do you want to update this definition further or accept it as is?\n"
            )
            return self.run_task_define("", state)
        else:
            self.con.print(f"\nAssistant: Let me know what you want this task to do\n")

        return state

    def run_task_edit(self, query_text: str, state: ChatState) -> ChatState:
        """
        We start with a chat thread containing a definition of what a task is.
        We then take the following steps:

            - in the 'task define' state we aim to produce a valid task definition JSON
            - in the 'task plan' step the agent suggests a step by step plan to write the task
            - in the 'task iterate' step we incrementally build out the script that runs the task

        """
        if state.mode == ChatMode.TaskDefine:
            return self.run_task_define(query_text, state)
        elif state.mode == ChatMode.TaskPlan:
            return self.run_task_plan(query_text, state)
        elif state.mode == ChatMode.TaskIterate:
            return self.run_task_iterate(query_text, state)
        else:
            raise ValueError(f"Invalid state for task definition: {state.mode}")

    def run_task_define(self, query_text: str, state: ChatState) -> ChatState:
        """
        Try to produce a valid task definition JSON.
        """
        proposed_task = None
        existing_task = self.tasks.get(state.task_slug)
        if existing_task and len(state.task_thread) == 2:
            proposed_task = existing_task

        if not proposed_task:
            state.task_thread.append(ChatMessage(role=Role.User, content=query_text))
            model = self.vendor.MODEL_OPTIONS[self.model_option]
            with Progress(transient=True) as progress:
                progress.add_task(
                    f"[red]Fetching response {self.vendor.MODEL_NAME} ({self.model_option})...",
                    start=False,
                    total=None,
                )
                message = self.vendor.chat(state.task_thread, model, max_tokens=8192)

            state.task_thread.append(message)
            self.con.print(f"\nAssistant:")
            formatted_text = Padding(escape(message.content), (1, 2))
            self.con.print(formatted_text, width=80)

            try:
                new_task = extract_task_meta(message.content)
            except Exception:
                new_task = None

            proposed_task = new_task

        if proposed_task:
            self.con.print(f"\n[bold cyan]Accept proposed task?[/bold cyan]")
            user_input = input("Enter y/N: ").strip().lower()
            if user_input == "y":
                self.con.print(
                    f"\n[bold cyan]Saving task definition for {state.task_slug}[/bold cyan]"
                )
                save_task(proposed_task)
                self.tasks = load_tasks()

                # TODO: initialise plan step (the rest of it)
                state.mode = ChatMode.TaskPlan
                self.task_step_initialised = False
                return state

        return state

    def run_task_plan(self, query_text: str, state: ChatState) -> ChatState:
        """
        The agent suggests a step by step plan to write the task
        """
        task = self.tasks.get(state.task_slug)
        # Faiil if there's no taskl
        plan = load_task_plan(task)

        # The agent suggests a step by step plan to write the task

        accepted = False
        if accepted:
            save_task_plan(plan)
            state.mode = ChatMode.TaskIterate

        return state

    def run_task_iterate(self, query_text: str, state: ChatState) -> ChatState:
        """
        - in the 'task iterate' step we incrementally build out the script that runs the task
            - read definition JSON and plan.txt
            - the agent suggests a change to the script that would execute the task
            - the agent can also ask the user to provide extra data required to write the script
            - the user can accept the change or suggest fixes
            - the agent runs the task so far and checks the result
            - the agent can delcare that the task code is written
            - the user has the opportunity to provide feedback
            - the user can accept completed task code
            - iterate again if not completed
            - write task python script once accepted

        """
        task = self.tasks.get(state.task_slug)
        # Faiil if there's no taskl
        plan = load_task_plan(task)
        # Fail if there's no plan
        pass

        # TODO: Implement this next

        # state.task_thread.append(ChatMessage(role=Role.User, content=query_text))
        # model = self.vendor.MODEL_OPTIONS[self.model_option]
        # with Progress(transient=True) as progress:
        #     progress.add_task(
        #         f"[red]Fetching response {self.vendor.MODEL_NAME} ({self.model_option})...",
        #         start=False,
        #         total=None,
        #     )
        #     message = self.vendor.chat(state.task_thread, model, max_tokens=8192)

        # state.task_thread.append(message)
        # self.con.print(f"\nAssistant:")
        # formatted_text = Padding(escape(message.content), (1, 2))
        # self.con.print(formatted_text, width=80)

        # if TASK_EXIT_TOKEN in message.content:
        #     try:
        #         task_meta = extract_task_meta(message.content)
        #     except Exception:
        #         self.con.print("[bold red]Error: Could not extract task metadata JSON[/bold red]")
        #         return state

        #     try:
        #         task_script = extract_task_script(message.content)
        #     except Exception:
        #         self.con.print("[bold red]Error: Could not extract Python script[/bold red]")
        #         return state

        #     save_task(task_meta, task_script)
        #     self.tasks = load_tasks()
        #     self.con.print(f"[green]Task '{task_meta.name} ({task_meta.slug})' created[/green]")
        #     state.mode = ChatMode.Chat

        return state
