import platform
import subprocess as sp

from rich.console import Console
from rich.padding import Padding
from rich.markup import escape
from rich.progress import Progress
import psutil

from src.schema import ChatMessage, Role
from .base import BaseAction


class ShellAction(BaseAction):

    def __init__(self, console: Console, vendor, model_option: str) -> None:
        super().__init__(console)
        self.vendor = vendor
        self.model_option = model_option

    def get_help_text(self) -> tuple[str, str]:
        return (
            "shell access",
            "\shell how much free disk space do I have",
        )

    def is_match(self, query_text: str) -> bool:
        return query_text.startswith(r"\shell ")

    def run(self, query_text: str, messages: list[ChatMessage]) -> list[ChatMessage]:
        goal = query_text[7:].strip()

        system_info = get_system_info()
        shell_instruction = f"""
        Write a single shell command to help the user achieve this goal in the context of this chat: {goal}
        Do not suggest shell commands that require interactive or TTY mode: these commands get run in a non-interactive subprocess.
        Include a brief explanation (1-2 sentences) of why you chose this shell command, but keep the explanation clearly separated from the command.
        Structure your response so that you start with the explanation and emit the shell command at the end.
        System info (take this into consideration):
        {system_info}
        """
        shell_msg = ChatMessage(role=Role.User, content=shell_instruction)
        messages.append(shell_msg)
        model = self.vendor.MODEL_OPTIONS[self.model_option]
        with Progress(transient=True) as progress:
            progress.add_task(
                f"[red]Generating shell command {self.vendor.MODEL_NAME} {self.model_option}...",
                start=False,
                total=None,
            )
            message = self.vendor.chat(messages, model)

        messages.append(message)
        self.con.print(f"\nAssistant:")
        formatted_text = Padding(escape(message.content), (1, 2))
        self.con.print(formatted_text, width=80)
        command_str = extract_shell_command(message.content, self.vendor, self.model_option)
        self.con.print(f"\n[bold yellow]Execute this command?[/bold yellow]")
        self.con.print(f"[bold cyan]{command_str}[/bold cyan]")
        user_input = input("Enter Y/n: ").strip().lower()

        if user_input == "y" or user_input == "":
            try:
                result = sp.run(command_str, shell=True, text=True, capture_output=True)
                output = f"Command: {command_str}\n\nExit Code: {result.returncode}"
                if result.stdout:
                    output += f"\n\nStdout:\n{result.stdout}"
                if result.stderr:
                    output += f"\n\nStderr:\n{result.stderr}"
                self.con.print(f"\n[bold blue]Shell Command Output:[/bold blue]")
                formatted_output = Padding(escape(output), (1, 2))
                self.con.print(formatted_output)
                messages.append(
                    ChatMessage(role=Role.User, content=f"Shell command executed:\n\n{output}")
                )
            except Exception as e:
                error_message = f"Error executing shell command: {str(e)}"
                self.con.print(f"\n[bold red]{error_message}[/bold red]")
                messages.append(ChatMessage(role=Role.User, content=error_message))

            # FIXME: Shell output is using a lot of tokens, could we swap it for just the followup message?
            followup_instruction = f"""
            Write a brief (1 sentence) followup commentary on the result of the execution of the command: {command_str}
            based on the user's original request: {goal}
            """
            followup_msg = ChatMessage(role=Role.User, content=followup_instruction)
            messages.append(followup_msg)

            with Progress(transient=True) as progress:
                progress.add_task(
                    f"[red]Analysing shell output {self.vendor.MODEL_NAME} {self.model_option}...",
                    start=False,
                    total=None,
                )
                message = self.vendor.chat(messages, model)

            messages.append(message)
            self.con.print(f"\nAssistant:")
            formatted_text = Padding(escape(message.content), (1, 2))
            self.con.print(formatted_text, width=80)
            return messages
        else:
            self.con.print("\n[bold yellow]Command execution cancelled.[/bold yellow]")
            cancel_message = f"Command execution cancelled by user."
            messages.append(ChatMessage(role=Role.User, content=cancel_message))
            return messages


def extract_shell_command(assistant_message: str, vendor, model_option: str) -> str:
    """
    Extract a shell command to be executed from the assistant's message
    """
    model = vendor.MODEL_OPTIONS[model_option]
    query_text = f"""
    Extract the proprosed shell command from this chat log.
    Return only a single shell command and nothing else.
    This is the chat log:
    {assistant_message}
    """
    return vendor.answer_query(query_text, model)


def get_system_info() -> str:
    system = platform.system()
    if system == "Windows":
        os_info = f"Windows {platform.release()}"
        additional_info = platform.win32_ver()
    elif system == "Darwin":
        os_info = f"macOS {platform.mac_ver()[0]}"
        additional_info = ", ".join(str(item) for item in platform.mac_ver()[1:])
    elif system == "Linux":
        os_info = f"Linux {platform.release()}"
        try:
            with open("/etc/os-release") as f:
                distro_info = dict(line.strip().split("=") for line in f if "=" in line)
            additional_info = distro_info.get("PRETTY_NAME", "").strip('"')
        except:
            additional_info = "Distribution information unavailable"
    else:
        os_info = f"Unknown OS: {system}"
        additional_info = "No additional information available"

    cpu_info = f"CPU: {platform.processor()}"
    ram = psutil.virtual_memory()
    ram_info = f"RAM: {ram.total // (1024**3)}GB total, {ram.percent}% used"
    disk = psutil.disk_usage("/")
    disk_info = f"Disk: {disk.total // (1024**3)}GB total, {disk.percent}% used"

    return f"{os_info}\n{additional_info}\n{cpu_info}\n{ram_info}\n{disk_info}"
