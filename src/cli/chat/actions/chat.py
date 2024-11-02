from rich.console import Console
from rich.progress import Progress
from rich.padding import Padding
from rich.markup import escape

from src.schema import ChatState, ChatMessage, Role, ChatMode, CommandOption
from .base import BaseAction


class ChatAction(BaseAction):

    cmd_options = [
        CommandOption(
            template="\chat",
            description="Return to chat",
            prefix="\chat",
        ),
    ]

    def __init__(self, console: Console, vendor, model_option: str) -> None:
        super().__init__(console)
        self.vendor = vendor
        self.model_option = model_option

    def is_match(self, query_text: str, state: ChatState, cmd_options: list[CommandOption]) -> bool:
        matches_other_cmd = self.matches_other_cmd(query_text, state, cmd_options)
        if matches_other_cmd:
            return False
        elif query_text == "\chat":
            return True
        elif state.mode == ChatMode.Chat:
            return bool(query_text)

    def run(self, query_text: str, state: ChatState) -> ChatState:
        if query_text == "\chat":
            return self.run_activate(query_text, state)
        else:
            return self.run_chat(query_text, state)

    def run_activate(self, query_text: str, state: ChatState) -> ChatState:
        state.mode = ChatMode.Chat
        self.con.print(f"\n[dim]Chat mode enabled[/dim]\n")
        return state

    def run_chat(self, query_text: str, state: ChatState) -> ChatState:
        model = self.vendor.MODEL_OPTIONS[self.model_option]
        state.messages.append(ChatMessage(role=Role.User, content=query_text))
        with Progress(transient=True) as progress:
            progress.add_task(
                f"[red]Asking {self.vendor.MODEL_NAME} {self.model_option}...",
                start=False,
                total=None,
            )
            message = self.vendor.chat(state.messages, model)

        state.messages.append(message)
        self.con.print(f"\nAssistant:")
        formatted_text = Padding(escape(message.content), (1, 2))
        self.con.print(formatted_text, width=80)
        return state
