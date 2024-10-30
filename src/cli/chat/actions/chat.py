from rich.console import Console
from rich.progress import Progress
from rich.padding import Padding
from rich.markup import escape

from src.schema import ChatMessage, Role
from .base import BaseAction


class ChatAction(BaseAction):

    def __init__(self, console: Console, vendor, model_option: str) -> None:
        super().__init__(console)
        self.vendor = vendor
        self.model_option = model_option

    def get_help_text(self) -> tuple[str, str]:
        return ("", "")  # Not used

    def is_match(self, query_text: str) -> bool:
        return bool(query_text)

    def run(self, query_text: str, messages: list[ChatMessage]) -> list[ChatMessage]:
        model = self.vendor.MODEL_OPTIONS[self.model_option]
        messages.append(ChatMessage(role=Role.User, content=query_text))
        with Progress(transient=True) as progress:
            progress.add_task(
                f"[red]Asking {self.vendor.MODEL_NAME} {self.model_option}...",
                start=False,
                total=None,
            )
            message = self.vendor.chat(messages, model)

        messages.append(message)
        self.con.print(f"\nAssistant:")
        formatted_text = Padding(escape(message.content), (1, 2))
        self.con.print(formatted_text, width=80)
        return messages
