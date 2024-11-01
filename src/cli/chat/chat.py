import click
from rich.padding import Padding
from rich.console import Console
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings

from src.settings import load_settings
from src.schema import ChatState, ChatMode, SshConfig
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
    SSHAction,
)

console = Console(width=100)

HELP_OPTIONS = {
    "submit": ["Enter"],
    "newline": ["CTRL-J"],
    "quit": ["CTRL-C, \q"],
    "help": ["\h"],
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
    state = ChatState(mode=ChatMode.Chat, messages=[], ssh_config=None)
    chat_action = ChatAction(console, vendor, model_option)
    actions = [
        ReadWebAction(console),
        ReadFileAction(console),
        ClearHistoryAction(console),
        CompressHistoryAction(console, vendor, model_option),
        # Last so it can catch all cmds in shell mode.
        ShellAction(console, vendor, model_option),
        SSHAction(console, vendor, model_option),
    ]
    print_help(actions, state)

    kb = build_key_bindings()

    while True:
        try:
            session = PromptSession(key_bindings=kb)
            query_text = session.prompt("\nYou: ", multiline=True, key_bindings=kb).strip()

            if query_text == r"\h":
                print_help(actions, state)
                continue

            if query_text == r"\q":
                console.print("\n\nAssistant: Bye 👋")
                return

            action_matched = False
            for action in actions:
                if action.is_match(query_text, state):
                    action_matched = True
                    state = action.run(query_text, state)
                    print_separator(state)
                    query_text = ""
                    break

            if action_matched:
                continue

            if chat_action.is_match(query_text, state):
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

    msg_prefix = f"\[{state.mode} mode]"
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

    console.print(f"{color_setting}{msg_prefix}{ssh_prefix}{separator}{msg_suffix}", style="dim")


def print_help(actions: list[BaseAction], state: ChatState):
    help_options = {**HELP_OPTIONS}
    for action in actions:
        if state.mode in action.active_modes:
            help_options[action.help_description] = action.help_examples

    max_key_length = max(len(key) for key in help_options) + 2  # for colon + space
    help_lines = []
    for k, v in help_options.items():
        if not v:
            continue

        action_desc = f"{k}: ".ljust(max_key_length)
        help_lines.append(f"{action_desc}{v[0]}")
        for val in v[1:]:
            space = f"".ljust(max_key_length)
            help_lines.append(f"{space}{val}")

    formatted_text = Padding("[green]" + "\n".join(help_lines), (1, 2))
    console.print(formatted_text)
