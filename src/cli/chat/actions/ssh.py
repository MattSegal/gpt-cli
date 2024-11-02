# WORK IN PROGRESS
import click
import paramiko
from rich.console import Console
from rich.padding import Padding
from rich.markup import escape
from rich.progress import Progress

from src.schema import ChatState, ChatMessage, Role, ChatMode, SshConfig, CommandOption
from .base import BaseAction

NO_COMMAND = "NO_COMMAND_EXTRACTED"


class SSHAction(BaseAction):
    cmd_options = [
        CommandOption(
            template=r"\ssh",
            description="Toggle ssh mode",
            prefix=r"\ssh",
        ),
        CommandOption(
            template="\ssh <query>",
            description="Run shell command via ssh",
            prefix="\ssh",
            example="\ssh how much free disk space do I have",
        ),
        CommandOption(
            template=r"\ssh connect",
            description="Connect to host",
            prefix=r"\ssh",
        ),
        CommandOption(
            template=r"\ssh disconnect",
            description="Disconnect from current host",
            prefix=r"\ssh",
        ),
    ]

    def __init__(self, console: Console, vendor, model_option: str) -> None:
        super().__init__(console)
        self.vendor = vendor
        self.model_option = model_option
        self.ssh_client = None
        self.system_info = None

    def is_match(self, query_text: str, state: ChatState, cmd_options: list[CommandOption]) -> bool:
        matches_other_cmd = self.matches_other_cmd(query_text, state, cmd_options)
        if matches_other_cmd:
            return False
        elif state.mode == ChatMode.Ssh:
            return bool(query_text)
        else:
            return query_text.startswith("\ssh")

    def run(self, query_text: str, state: ChatState) -> ChatState:
        if query_text == r"\ssh connect":
            return self.run_connect(query_text, state)
        elif query_text == r"\ssh disconnect":
            return self.run_disconnect(query_text, state)
        elif state.mode == ChatMode.Ssh and query_text == "\ssh":
            return self.run_deactivate(query_text, state)
        elif state.mode != ChatMode.Ssh and query_text == "\ssh":
            return self.run_activate(query_text, state)
        else:
            return self.run_command(query_text, state)

    def run_connect(self, query_text: str, state: ChatState) -> ChatState:
        if state.mode != ChatMode.Ssh:
            state.mode = ChatMode.Ssh
            self.con.print(f"\n[bold magenta]SSH mode enabled[/bold magenta]\n")

        state.ssh_config = self.setup_ssh_config()
        is_success, connect_msg = self.connect_ssh(state.ssh_config)
        if is_success:
            self.con.print(f"[magenta]{connect_msg}[/magenta]\n")
        else:
            self.con.print(f"[yellow]{connect_msg}[/yellow]\n")
            state.mode = ChatMode.Chat
            self.con.print(f"\n[bold magenta]SSH mode disabled[/bold magenta]\n")

        return state

    def run_disconnect(self, query_text: str, state: ChatState) -> ChatState:
        state.ssh_config = None
        if state.mode == ChatMode.Ssh:
            state.mode = ChatMode.Chat

        if not self.ssh_client:
            self.con.print("\n[bold yellow]Not connected to any SSH host[/bold yellow]\n")
        else:
            self.ssh_client.close()
            self.ssh_client = None
            self.con.print("\n[bold magenta]Disconnected from SSH host[/bold magenta]\n")

        return state

    def run_activate(self, query_text: str, state: ChatState) -> ChatState:
        self.con.print(f"\n[bold magenta]SSH mode enabled[/bold magenta]\n")
        state.mode = ChatMode.Ssh
        if not state.ssh_config:
            state.ssh_config = self.setup_ssh_config()

        if not self.ssh_client:
            self.connect_ssh(state.ssh_config)
            is_success, connect_msg = self.connect_ssh(state.ssh_config)
            if is_success:
                self.con.print(f"[magenta]{connect_msg}[/magenta]\n")
            else:
                self.con.print(f"[yellow]{connect_msg}[/yellow]\n")
                state.mode = ChatMode.Chat
                self.con.print(f"\n[bold magenta]SSH mode disabled[/bold magenta]\n")

        return state

    def run_deactivate(self, query_text: str, state: ChatState) -> ChatState:
        state.mode = ChatMode.Chat
        self.con.print(f"\n[bold magenta]SSH mode disabled[/bold magenta]\n")
        return state

    def get_system_info(self):
        command_str = (
            "(cat /etc/os-release 2>/dev/null || cat /etc/issue 2>/dev/null || echo "
            ") && uname -a"
        )
        _, stdout, _ = self.ssh_client.exec_command(command_str)
        return stdout.read().decode()

    def run_command(self, query_text: str, state: ChatState) -> ChatState:
        if not self.ssh_client:
            self.con.print("\n[bold red]Not connected to any SSH host.[/bold red]\n")
            return state

        goal = query_text.strip()
        if query_text.startswith(r"\ssh "):
            goal = query_text[5:].strip()

        ssh_instruction = f"""
        Write a single shell command to help the user achieve this goal in the context of this chat: {goal}
        Do not suggest shell commands that require interactive or TTY mode: these commands get run in a non-interactive subprocess.
        Include a brief explanation (1-2 sentences) of why you chose this shell command, but keep the explanation clearly separated from the command.
        Structure your response so that you start with the explanation and emit the shell command at the end.

        This command will be executed over SSH on remote host {state.ssh_config.conn_name}
        You do not need to SSH into the host that has been taken care of. 
        Host system info (take this into consideration):
        {self.system_info}
        """

        ssh_msg = ChatMessage(role=Role.User, content=ssh_instruction)
        state.messages.append(ssh_msg)
        model = self.vendor.MODEL_OPTIONS[self.model_option]

        with Progress(transient=True) as progress:
            progress.add_task(
                f"[red]Generating SSH command {self.vendor.MODEL_NAME} {self.model_option}...",
                start=False,
                total=None,
            )
            message = self.vendor.chat(state.messages, model)

        state.messages.append(message)
        self.con.print(f"\nAssistant:")
        formatted_text = Padding(escape(message.content), (1, 2))
        self.con.print(formatted_text, width=80)

        command_str = extract_ssh_command(message.content, self.vendor, self.model_option)
        if command_str == NO_COMMAND:
            no_extract_msg = "No command could be extracted"
            self.con.print(f"\n[bold yellow]{no_extract_msg}[/bold yellow]")
            state.messages.append(ChatMessage(role=Role.User, content=no_extract_msg))
            return state

        self.con.print(
            f"\n[bold yellow]Execute this command on {state.ssh_config.conn_name}?[/bold yellow]"
        )
        self.con.print(f"[bold cyan]{command_str}[/bold cyan]")
        user_input = input("Enter Y/n: ").strip().lower()

        if user_input == "y" or user_input == "":
            try:
                stdin, stdout, stderr = self.ssh_client.exec_command(command_str)
                stdout_str = stdout.read().decode()
                stderr_str = stderr.read().decode()
                exit_code = stdout.channel.recv_exit_status()

                output = f"Command: {command_str}\n\nExit Code: {exit_code}"
                if stdout_str:
                    output += f"\n\nStdout:\n{stdout_str}"
                if stderr_str:
                    output += f"\n\nStderr:\n{stderr_str}"

                self.con.print(f"\n[bold blue]SSH Command Output:[/bold blue]")
                formatted_output = Padding(escape(output), (1, 2))
                self.con.print(formatted_output)
                state.messages.append(
                    ChatMessage(role=Role.User, content=f"SSH command executed:\n\n{output}")
                )

                followup_instruction = f"""
                Write a brief (1 sentence) followup commentary on the result of the execution of the command: {command_str}
                based on the user's original request: {goal}
                """
                followup_msg = ChatMessage(role=Role.User, content=followup_instruction)
                state.messages.append(followup_msg)

                with Progress(transient=True) as progress:
                    progress.add_task(
                        f"[red]Analysing SSH output {self.vendor.MODEL_NAME} {self.model_option}...",
                        start=False,
                        total=None,
                    )
                    message = self.vendor.chat(state.messages, model)

                state.messages.append(message)
                self.con.print(f"\nAssistant:")
                formatted_text = Padding(escape(message.content), (1, 2))
                self.con.print(formatted_text, width=80)

            except Exception as e:
                error_message = f"Error executing SSH command: {str(e)}"
                self.con.print(f"\n[bold red]{error_message}[/bold red]")
                state.messages.append(ChatMessage(role=Role.User, content=error_message))

        else:
            self.con.print("\n[bold yellow]Command execution cancelled.[/bold yellow]")
            cancel_message = "Command execution cancelled by user."
            state.messages.append(ChatMessage(role=Role.User, content=cancel_message))

        return state

    def setup_ssh_config(self) -> SshConfig:
        self.con.print("[yellow]Setup SSH Config[/yellow]")
        host = click.prompt("Host", type=str)
        username = click.prompt("Username", type=str)
        port = click.prompt("Port", type=int, default=22)
        return SshConfig(host=host, username=username, port=port)

    def connect_ssh(self, ssh_config: SshConfig) -> tuple[bool, str]:
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh_client.connect(
                hostname=ssh_config.host, port=ssh_config.port, username=ssh_config.username
            )
            self.current_host = f"{ssh_config.username}@{ssh_config.host}"
            self.system_info = self.get_system_info()
            return True, f"Connected to {self.current_host}"
        except Exception as e:
            return False, f"SSH connection failed: {str(e)}"


def extract_ssh_command(assistant_message: str, vendor, model_option: str) -> str:
    """
    Extract an SSH command to be executed from the assistant's message
    """
    model = vendor.MODEL_OPTIONS[model_option]
    query_text = f"""
    Extract the proposed SSH command from this chat log.
    Return only a single command and nothing else.
    This is the chat log:
    {assistant_message}

    If there is not any command to extract then return only the exact string {NO_COMMAND}
    """
    return vendor.answer_query(query_text, model)
