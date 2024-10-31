from src.schema import ChatState, ChatMode
from .base import BaseAction


class ClearHistoryAction(BaseAction):

    help_description = "clear chat"
    help_examples = ["\c"]
    active_modes = [ChatMode.Chat, ChatMode.Shell]

    def is_match(self, query_text: str, state: ChatState) -> bool:
        return query_text == r"\c" and state.mode in self.active_modes

    def run(self, query_text: str, state: ChatState) -> ChatState:
        self.con.print("\n[bold green]Chat history cleared.[/bold green]")
        state.messages = []
        return state
