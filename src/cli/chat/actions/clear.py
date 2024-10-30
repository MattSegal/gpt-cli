from src.schema import ChatState
from .base import BaseAction


class ClearHistoryAction(BaseAction):

    def get_help_text(self) -> tuple[str, str]:
        return (
            "clear chat",
            "\c",
        )

    def is_match(self, query_text: str) -> bool:
        return query_text == r"\c"

    def run(self, query_text: str, state: list[ChatState]) -> list[ChatState]:
        self.con.print("\n[bold green]Chat history cleared.[/bold green]")
        state.messages = []
        return state
