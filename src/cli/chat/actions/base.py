from rich.console import Console

from src.schema import ChatMessage


class BaseAction:

    def __init__(self, console: Console) -> None:
        self.con = console

    def get_help_text(self) -> tuple[str, str]:
        raise NotImplementedError()

    def is_match(self, query_text: str) -> bool:
        raise NotImplementedError()

    def run(self, query_text: str, messages: list[ChatMessage]) -> list[ChatMessage]:
        raise NotImplementedError()
