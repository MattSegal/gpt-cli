import subprocess as sp
import platform

import click
import psutil
from rich.padding import Padding
from rich.markup import escape
from rich.progress import Progress
from rich.console import Console
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings

from src.web import fetch_text_for_url
from src.settings import load_settings
from src.schema import ChatMessage, Role
from src import vendors
from .cli import cli

console = Console(width=100)


@cli.command()
@click.argument("text", nargs=-1, required=False)
def chat(text: tuple[str, ...]):
    """
    Continue chat after initial ask

    \b
    Examples:
      ask chat
      ask chat how do I flatten a list in python

    """
    settings = load_settings()

    # Initialize with stdin/argument text if provided
    query_text = " ".join(text)
    if settings.ANTHROPIC_API_KEY:
        vendor = vendors.anthropic
    elif settings.OPENAI_API_KEY:
        vendor = vendors.openai
    else:
        raise click.ClickException("Set either ANTHROPIC_API_KEY or OPENAI_API_KEY as envars")

    model_option = vendor.DEFAULT_MODEL_OPTION
    model = vendor.MODEL_OPTIONS[model_option]
    console.print(f"[green]Chatting with {vendor.MODEL_NAME} {model_option}")
    print_help()

    if query_text:
        console.print(f"\nYou:", escape(query_text), "\n")
        messages = [ChatMessage(role=Role.User, content=query_text)]
    else:
        messages = []

    kb = build_key_bindings()
    while True:
        if messages:
            with Progress(transient=True) as progress:
                progress.add_task(
                    f"[red]Asking {vendor.MODEL_NAME} {model_option}...",
                    start=False,
                    total=None,
                )
                message = vendor.chat(messages, model)

            messages.append(message)
            console.print(f"\nAssistant:")
            formatted_text = Padding(escape(message.content), (1, 2))
            console.print(formatted_text, width=80)
            console.print("-" * console.width, style="dim")

        try:

            query_text = ""
            while not query_text:
                session = PromptSession(key_bindings=kb)
                query_text = session.prompt("\nYou: ", multiline=True, key_bindings=kb)
                query_text = query_text.strip()

                if query_text.startswith(r"\web "):
                    query_text = run_web_query(query_text, messages)
                    continue

                if query_text.startswith(r"\file "):
                    query_text = run_file_query(query_text, messages)
                    continue

                if query_text.startswith(r"\shell "):
                    query_text = run_shell_query(query_text, messages, vendor, model_option)
                    continue

                if query_text == r"\c":
                    messages = []
                    console.print("\n[bold green]Chat history cleared.[/bold green]")
                    query_text = ""
                    continue

                if query_text == r"\h":
                    print_help()
                    query_text = ""
                    continue
                if query_text == r"\q":
                    console.print("\n\nAssistant: Bye 👋")
                    return

            messages.append(ChatMessage(role=Role.User, content=query_text))

        except (KeyboardInterrupt, click.exceptions.Abort):
            console.print("\n\nAssistant: Bye 👋")
            return


def build_key_bindings():
    kb = KeyBindings()

    @kb.add("enter")
    def _(event):
        """Submit on any enter press"""
        buf = event.current_buffer
        buf.validate_and_handle()

    @kb.add("c-j")
    def _(event):
        """Insert a newline character on Ctrl+J"""
        event.current_buffer.insert_text("\n")

    return kb


def run_shell_query(query_text: str, messages: list[ChatMessage], vendor, model_option: str) -> str:
    goal = query_text[7:].strip()

    system_info = get_system_info()
    shell_instruction = f"""
    Write a single shell command to help the user achieve this goal in the context of this chat: {goal}
    Include a brief explanation (1-2 sentences) of why you chose this shell command, but keep the explanation clearly separated from the command.
    Structure your response so that you start with the explanation and emit the shell command at the end.
    System info (take this into consideration):
    {system_info}
    """
    shell_msg = ChatMessage(role=Role.User, content=shell_instruction)
    messages.append(shell_msg)
    model = vendor.MODEL_OPTIONS[model_option]
    with Progress(transient=True) as progress:
        progress.add_task(
            f"[red]Generating shell command {vendor.MODEL_NAME} {model_option}...",
            start=False,
            total=None,
        )
        message = vendor.chat(messages, model)

    messages.append(message)
    console.print(f"\nAssistant:")
    formatted_text = Padding(escape(message.content), (1, 2))
    console.print(formatted_text, width=80)

    command_str = extract_shell_command(message.content, vendor, model_option)
    console.print(f"\n[bold yellow]Execute this command?[/bold yellow]")
    console.print(f"[bold cyan]{command_str}[/bold cyan]")
    user_input = input("Enter Y/n: ").strip().lower()

    if user_input == "y" or user_input == "":
        try:
            result = sp.run(command_str, shell=True, text=True, capture_output=True)
            output = f"Command: {command_str}\n\nExit Code: {result.returncode}"
            if result.stdout:
                output += f"\n\nStdout:\n{result.stdout}"
            if result.stderr:
                output += f"\n\nStderr:\n{result.stderr}"
            console.print(f"\n[bold blue]Shell Command Output:[/bold blue]")
            formatted_output = Padding(escape(output), (1, 2))
            console.print(formatted_output)
            messages.append(
                ChatMessage(role=Role.User, content=f"Shell command executed:\n\n{output}")
            )
        except Exception as e:
            error_message = f"Error executing shell command: {str(e)}"
            console.print(f"\n[bold red]{error_message}[/bold red]")
            messages.append(ChatMessage(role=Role.User, content=error_message))

        followup_instruction = f"""
        Write a brief (1 sentence) followup commentary on the result of the execution of the command: {command_str}
        based on the user's original request: {goal}
        """
        followup_msg = ChatMessage(role=Role.User, content=followup_instruction)
        messages.append(followup_msg)

        with Progress(transient=True) as progress:
            progress.add_task(
                f"[red]Analysing shell output {vendor.MODEL_NAME} {model_option}...",
                start=False,
                total=None,
            )
            message = vendor.chat(messages, model)

        messages.append(message)
        console.print(f"\nAssistant:")
        formatted_text = Padding(escape(message.content), (1, 2))
        console.print(formatted_text, width=80)
        query_text = ""
        return query_text

    else:
        console.print("\n[bold yellow]Command execution cancelled.[/bold yellow]")
        cancel_message = f"Command execution cancelled by user."
        messages.append(ChatMessage(role=Role.User, content=cancel_message))
        query_text = ""
        return query_text


def run_file_query(query_text: str, messages: list[ChatMessage]) -> str:
    file_path = query_text[6:].strip()
    try:
        with open(file_path, "r") as file:
            file_content = file.read()
        console.print(f"\n[bold blue]Content from {file_path}:[/bold blue]")
        max_char = 512
        if len(file_content) > max_char:
            file_content_display = file_content[:512] + "..."
        else:
            file_content_display = file_content

        formatted_text = Padding(escape(file_content_display), (1, 2))
        console.print(formatted_text)
        file_content_length = len(file_content)
        query_text = (
            f"Content from {file_path} ({file_content_length} chars total):\n\n{file_content}"
        )
        messages.append(ChatMessage(role=Role.User, content=query_text))
        query_text = ""
        return query_text
    except FileNotFoundError:
        console.print(f"\n[bold red]Error: File '{file_path}' not found.[/bold red]")
        query_text = ""
        return query_text
    except IOError:
        console.print(f"\n[bold red]Error: Unable to read file '{file_path}'.[/bold red]")
        query_text = ""
        return query_text


def run_web_query(query_text: str, messages: list[ChatMessage]) -> str:
    url = query_text[5:].strip()
    url_text = fetch_text_for_url(url)
    console.print(f"\n[bold blue]Content from {url}:[/bold blue]")
    max_char = 512
    if len(url_text) > max_char:
        url_text_display = url_text[:512] + "..."
    else:
        url_text_display = url_text

    formatted_text = Padding(escape(url_text_display), (1, 2))
    console.print(formatted_text)
    url_text_length = len(url_text)
    query_text = f"Content from {url} ({url_text_length} chars total):\n\n{url_text}"
    messages.append(ChatMessage(role=Role.User, content=query_text))
    query_text = ""
    return query_text


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


HELP_OPTIONS = {
    "quit": "CTRL-C or \q",
    "clear chat": "\c",
    "newline": "CTRL-J",
    "shell access": "\shell how much free disk space do I have",
    "read file": "\\file /etc/hosts",
    "fetch web text": "\web example.com",
    "help": "\h",
}


def print_help():
    max_key_length = max(len(key) for key in HELP_OPTIONS)
    help_text = [
        f"[green]{key.ljust(max_key_length)}:  {value}" for key, value in HELP_OPTIONS.items()
    ]
    formatted_text = Padding("\n".join(help_text), (1, 2))
    console.print(formatted_text)


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
