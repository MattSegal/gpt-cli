from src.schema import ChatMessage
from .base import BaseAction


class ClearHistoryAction(BaseAction):

    def get_help_text(self) -> tuple[str, str]:
        return (
            "clear chat",
            "\c",
        )

    def is_match(self, query_text: str) -> bool:
        return query_text == r"\c"

    def run(self, query_text: str, messages: list[ChatMessage]) -> list[ChatMessage]:
        self.con.print("\n[bold green]Chat history cleared.[/bold green]")
        return []
