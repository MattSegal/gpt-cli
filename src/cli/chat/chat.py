import click
from rich.padding import Padding
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings

from src.settings import load_settings
from src.schema import ChatState, ChatMode, CommandOption
from src import vendors
from ..cli import cli
from .actions import (
    ReadFileAction,
    ReadWebAction,
    CompressHistoryAction,
    ClearHistoryAction,
    ShellAction,
    ChatAction,
    TaskAction,
    SSHAction,
)

console = Console(width=100)

CMD_OPTIONS = [
    CommandOption(template="Enter", description="Submit"),
    CommandOption(template="CTRL-J", description="New line"),
    CommandOption(template="CTRL-C, \\q", description="Quit", prefix="\\q"),
    CommandOption(template="\\h", description="Show help", prefix="\\h"),
]


@cli.command()
def chat():
    """
    Start an ongoing chat

    \b
    Examples:
      ask chat

    """
    settings = load_settings()
    if settings.ANTHROPIC_API_KEY:
        vendor = vendors.anthropic
    elif settings.OPENAI_API_KEY:
        vendor = vendors.openai
    else:
        raise click.ClickException("Set either ANTHROPIC_API_KEY or OPENAI_API_KEY as envars")

    model_option = vendor.DEFAULT_MODEL_OPTION
    console.print(f"[green]Chatting with {vendor.MODEL_NAME} {model_option}")
    state = ChatState(
        mode=ChatMode.Chat,
        messages=[],
        ssh_config=None,
        task_thread=[],
        task_slug=None,
    )
    actions = [
        ReadWebAction(console),
        ReadFileAction(console),
        ClearHistoryAction(console),
        CompressHistoryAction(console, vendor, model_option),
        # Last so it can catch all cmds in shell mode.
        ChatAction(console, vendor, model_option),
        ShellAction(console, vendor, model_option),
        SSHAction(console, vendor, model_option),
        TaskAction(console, vendor, model_option),
    ]
    cmd_options = [*CMD_OPTIONS]
    for action in actions:
        cmd_options.extend(action.cmd_options)

    print_help(cmd_options)

    kb = build_key_bindings()

    while True:
        try:
            session = PromptSession(key_bindings=kb)
            query_text = session.prompt("\nYou: ", multiline=True, key_bindings=kb).strip()

            if query_text == r"\h":
                print_help(cmd_options)
                continue

            if query_text == r"\q":
                console.print("\n\nAssistant: Bye 👋")
                return

            for action in actions:
                if action.is_match(query_text, state, cmd_options):
                    state = action.run(query_text, state)
                    print_separator(state)
                    query_text = ""
                    break

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


def print_separator(state: ChatState):
    if state.mode.startswith(ChatMode._TaskPrefix):
        messages = state.task_thread
    else:
        messages = state.messages

    num_messages = len(messages)
    total_chars = sum(len(m.content) for m in messages)

    mode_display = state.mode.replace("_", " ")
    msg_prefix = f"\[{mode_display} mode]"
    ssh_prefix = ""
    if state.ssh_config is not None:
        ssh_prefix = f"\[connected to {state.ssh_config.conn_name}]"

    msg_suffix = f" [{num_messages} msgs, {total_chars} chars]"
    separator = "-" * (console.width - len(msg_prefix) - len(msg_suffix) - len(ssh_prefix))

    color_setting = ""
    if state.mode == ChatMode.Shell:
        color_setting = "[yellow]"
    if state.mode == ChatMode.Ssh:
        color_setting = "[magenta]"
    if state.mode.startswith(ChatMode._TaskPrefix):
        color_setting = "[cyan]"

    console.print(f"{color_setting}{msg_prefix}{ssh_prefix}{separator}{msg_suffix}", style="dim")


def print_help(cmd_options: list[CommandOption]):
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Command", style="green")
    table.add_column("Description", style="dim")
    table.add_column("Example", style="dim")
    for cmd_option in cmd_options:
        table.add_row(
            cmd_option.template,
            cmd_option.description,
            cmd_option.example,
        )

    console.print(Panel(table, title="Commands", border_style="dim"))
