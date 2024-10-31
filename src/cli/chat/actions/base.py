from rich.console import Console

from src.schema import ChatState, ChatMode


class BaseAction:

    help_description: str
    help_examples: list[str]
    active_modes: list[ChatMode]

    def __init__(self, console: Console):
        self.con = console

    def is_match(self, query_text: str, state: ChatState) -> bool:
        raise NotImplementedError()

    def run(self, query_text: str, state: ChatState) -> ChatState:
        raise NotImplementedError()
