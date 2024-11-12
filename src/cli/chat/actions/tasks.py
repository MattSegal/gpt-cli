import re
import sys
import json

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress
from rich.markup import escape
from rich.padding import Padding


from src.schema import ChatState, ChatMessage, Role, ChatMode, CommandOption, TaskMeta
from src.tasks import load_tasks, save_task, delete_task, run_task, TOOLS

from .base import BaseAction
from .shell import get_system_info


class TaskAction(BaseAction):

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
        self.task_thread = []

    def is_match(self, query_text: str, state: ChatState, cmd_options: list[CommandOption]) -> bool:
        matches_other_cmd = self.matches_other_cmd(query_text, state, cmd_options)
        if matches_other_cmd:
            return False
        elif state.mode == ChatMode.Task:
            return bool(query_text)
        else:
            return query_text.startswith("\\task")

    def run(self, query_text: str, state: ChatState) -> ChatState:
        if query_text == "\\task list":
            return self.run_list_tasks(query_text, state)
        elif query_text.startswith("\\task delete"):
            return self.run_delete_task(query_text, state)
        elif query_text.startswith("\\task update"):
            return self.run_update_task(query_text, state)
        elif query_text.startswith("\\task inspect"):
            return self.run_inspect_task(query_text, state)
        elif query_text.startswith("\\task create"):
            return self.run_create_task(query_text, state)
        elif query_text.startswith("\\task run"):
            return self.run_task(query_text, state)
        else:
            # We're in task mode running create or update
            return self.run_task_mode(query_text, state)

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

    def run_update_task(self, query_text: str, state: ChatState) -> ChatState:
        self.con.print("[green]run_update_task[/green]")
        return state

    def run_inspect_task(self, query_text: str, state: ChatState) -> ChatState:
        self.con.print("[green]run_inspect_task[/green]")
        return state

    def run_create_task(self, query_text: str, state: ChatState) -> ChatState:
        slug = query_text.split()[-1]
        if not slug:
            self.con.print(
                f"\n[bold red]Error: You must provide a slug for your new task[/bold red]"
            )

        if any(task_slug == slug for task_slug in self.tasks):
            self.con.print(f"\n[bold red]Error: Task with slug '{slug}' already exists[/bold red]")
            return state

        python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        dependencies_json = json.dumps(
            {slug: task.model_dump() for slug, task in self.tasks.items()}
        )
        tools_json = json.dumps({slug: task.to_schema() for slug, task in TOOLS.items()}, indent=2)
        instruction = TASK_MODE_ENTRY_INSTRUCTION.format(
            slug=slug,
            system_info=self.system_info,
            python_version=python_version,
            dependencies_json=dependencies_json,
            tools_json=tools_json,
            task_exit_token=TASK_EXIT_TOKEN,
        )
        self.task_thread = [*state.messages, ChatMessage(role=Role.User, content=instruction)]
        state.mode = ChatMode.Task
        self.con.print(
            f"\n[bold cyan]Task creation mode: describe what you want to do[/bold cyan]\n"
        )
        return state

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

    def run_task_mode(self, query_text: str, state: ChatState) -> ChatState:
        self.task_thread.append(ChatMessage(role=Role.User, content=query_text))
        model = self.vendor.MODEL_OPTIONS[self.model_option]
        with Progress(transient=True) as progress:
            progress.add_task(
                f"[red]Fetching response {self.vendor.MODEL_NAME} ({self.model_option})...",
                start=False,
                total=None,
            )
            message = self.vendor.chat(self.task_thread, model, max_tokens=8192)

        self.task_thread.append(message)
        self.con.print(f"\nAssistant:")
        formatted_text = Padding(escape(message.content), (1, 2))
        self.con.print(formatted_text, width=80)

        if TASK_EXIT_TOKEN in message.content:
            try:
                task_meta = extract_task_meta(message.content)
            except Exception:
                self.con.print("[bold red]Error: Could not extract task metadata JSON[/bold red]")
                return state

            try:
                task_script = extract_task_script(message.content)
            except Exception:
                self.con.print("[bold red]Error: Could not extract Python script[/bold red]")
                return state

            save_task(task_meta, task_script)
            self.tasks = load_tasks()
            self.con.print(f"[green]Task '{task_meta.name} ({task_meta.slug})' created[/green]")
            state.mode = ChatMode.Chat

        return state


def extract_task_meta(message: str) -> TaskMeta:
    json_match = re.search(r"```json\s*(.*?)\s*```", message, re.DOTALL)
    task_meta = json.loads(json_match.group(1))
    return TaskMeta(**task_meta)


def extract_task_script(message: str) -> str:
    python_match = re.search(r"```python\s*(.*?)\s*```", message, re.DOTALL)
    return python_match.group(1)


TASK_EXIT_TOKEN = "TASK_GENERATION_COMPLETE"


TASK_DEFINITION_INSTRUCTION = """
You are now in "Task Mode"

Your job is to generate a "task" in an interactive chat session with a user.
A task is a single-file python script with well defined inputs and outputs and some metadata.

# Task Definition

The following data is required to define a task:

- A JSON object defining the task metadata
- a Python script which contains the task's `run` function

## Task Metadata

The metadata for a task takes the following form (JSON schema): 

```json
{{
    "type": "object",
    "properties": {{
        "name": {{
            "type": "string"
        }},
        "description": {{
            "type": "string"
        }},
        "summary": {{
            "type": "string"
        }},
        "slug": {{
            "type": "string"
        }},
        "input_schema": {{
            "type": "object"
        }},
        "output_schema": {{
            "type": "object"
        }},
        "depends_on": {{
            "type": "array",
            "items": {{
                "type": "string"
            }}
        }}
    }},
    "required": ["name", "description", "summary", "slug", "input_schema", "output_schema", "depends_on"]
}}
```

Here's some details on what these fields mean:

- name: user friendly name for the task
- description: short description of what the task does
- summary: longer description of how the task achieves its goal
- slug: unique task slug
- input_schema: JSON schema description of the task's `run` function input
- output_schema: JSON schema description of the task's `run` function output
- depends_on: list of other task slugs that this task depends on (and makes use of)

## Input/Output Schema Requirements:

A task's input schema must be an object (ie. Python dict).
The dictionary must not have any nested objects.
It is expected that a human can reasonably specify all the data required for the schema froma CLI.
The input schema may be an empty object if there are no inputs to the task.

A task's output schema must be an object (ie. Python dict).
There are no limits to the complexity of the output schema.


## Task Python Script

A valid task script contains a `run` function with the following signature:

```python

def run(input_data: dict, dependencies: dict, tools: dict) -> dict:
    pass # Task implemented here

```

The input_data and output dict of the `run` function are defined by the
JSON schema in the task metadata. Task do not need to validate their inputs or outputs
according to the defined schemas: this is handled elsewhere.

The script uses Python version {python_version}
This script may define whatever functions/classes/data structrues are necessary to do the job.
Docstrings and comments are nice to have but not mandatory.
The script should not require any user input beyond the input data provided.
The script may also make use of the Python standard library.
The script may also make use of the following 3rd party libraries:

- requests = "^2.32.3"
- trafilatura = "^1.12.2"
- beautifulsoup4 = "^4.12.3"
- html5lib = "^1.1"
- pypdf = "^5.0.1"
- lxml-html-clean = "^0.3.1"
- psutil = "^6.1.0"

## Error handling

Task should handle their own exceptions. They should not throw unhandled exceptions.
Error reporting should be done by including a "success" boolean in the output data,
as appropriate, and a descriptive "fail_reason" string in the output data, as appropriate.


## External Communications

Tasks are allowed and expected to make external API calls when needed. This includes:
- HTTP requests to external services
- API integrations
- Web scraping
- File downloads
- Network connections

Tasks should handle external communication failures gracefully and report them through the standard error reporting mechanism (success/fail_reason).
Note that while external calls are allowed, tasks should be respectful of rate limits and implement appropriate error handling for network failures.


## Task Dependenices

A task can make use of other tasks which already have been created.
If another task is used by this task then its slug must be included in the "depends_on"
field in the task metadata. 

The task's `run` function will be passed a `dependencies` dict where the keys are the
the slug of a task to be used and the values are the run functions of those tasks. 

These are the tasks that may be used as depednencies:

```json
{dependencies_json}
```


## Task Tools

In addition to other tasks you can make use of a set of pre-defined tools.
The task's `run` function will be passed a `tools` dict where the keys are the
the slug of a tool to be used and the values are the functions that run the tools. 

These are the tools avaiable:

```json
{tools_json}
```


## Example task script

Here is an example task Python script:

```python
import requests

def run(input_data: dict, dependencies: dict, tools: dict) -> dict:
    url = input_data["url"] 

    # Fetch URL text (using 'web' tool)
    fetch_url_text = tools["web"]
    try:
        url_text = fetch_text_for_url(url)
    except Exception:
        return {{"success": False, "fail_reason": "Failed to fetch text from URL"}}

    # Classify URL text (using 'classify-text' task dependency)
    # Note: this is not a real dependency, this is just an illustrative example.
    classify_text = dependencies["classify-text"]
    try:
        text_classification = classify_text(url_text)
    except Exception:
        return {{"success": False, "fail_reason": "Failed to classify URL text"}}
    
    # Send success notification
    requests.post("https://example.com/api/notify", json={{
        "user": "matt",
        "message": f"Successfully classified {{url}}",
    }})

    return {{"success": True, "classification": text_classification}}

```


# System Information

System info (take this into consideration): 
{system_info}

# Chat Mode

You are to engage with an interactive, iterative chat with the user 
in order to define the task goals and behaviours. Do not print code
snippets, this is a high level discussion about what the task should achieve
and its interface. You may print the input and output JSON schema for clarification.

Once you are confident that you understand what you need to do, print a
final message containing:

- A JSON object defining the task metadata
- a Python script which contains the task's `run` function
- The exit string {task_exit_token}
"""
