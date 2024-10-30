import click
from rich.padding import Padding
from rich.console import Console
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings

from src.settings import load_settings
from src.schema import ChatState
from src import vendors
from ..cli import cli
from .actions import (
    ReadFileAction,
    ReadWebAction,
    CompressHistoryAction,
    ClearHistoryAction,
    ShellAction,
    ChatAction,
    BaseAction,
)

console = Console(width=100)

HELP_OPTIONS = {
    "submit": "Enter",
    "newline": "CTRL-J",
    "quit": "CTRL-C or \q",
    "help": "\h",
}


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
    chat_action = ChatAction(console, vendor, model_option)
    actions = [
        ShellAction(console, vendor, model_option),
        ReadWebAction(console),
        ReadFileAction(console),
        ClearHistoryAction(console),
        CompressHistoryAction(console, vendor, model_option),
    ]
    print_help(actions)

    kb = build_key_bindings()

    state = ChatState(is_shell_active=False, messages=[])
    while True:
        try:
            session = PromptSession(key_bindings=kb)
            query_text = session.prompt("\nYou: ", multiline=True, key_bindings=kb).strip()

            action_matched = False
            for action in actions:
                if action.is_match(query_text):
                    action_matched = True
                    state = action.run(query_text, state)
                    print_separator(state)
                    query_text = ""
                    break

            if action_matched:
                continue

            if query_text == r"\h":
                print_help(actions)
                continue

            if query_text == r"\q":
                console.print("\n\nAssistant: Bye 👋")
                return

            if chat_action.is_match(query_text):
                state = chat_action.run(query_text, state)
                print_separator(state)

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
    num_messages = len(state.messages)
    total_chars = sum(len(m.content) for m in state.messages)
    msg_text = f" [{num_messages} msgs, {total_chars} chars]"
    separator = "-" * (console.width - len(msg_text))
    console.print(f"{separator}{msg_text}", style="dim")


def print_help(actions: list[BaseAction]):
    help_options = {**HELP_OPTIONS}
    for action in actions:
        k, v = action.get_help_text()
        help_options[k] = v

    max_key_length = max(len(key) for key in help_options)
    help_text = [
        f"[green]{key.ljust(max_key_length)}:  {value}" for key, value in help_options.items()
    ]
    formatted_text = Padding("\n".join(help_text), (1, 2))
    console.print(formatted_text)
