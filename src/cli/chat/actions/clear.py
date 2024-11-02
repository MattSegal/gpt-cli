from src.schema import ChatState, ChatMode, CommandOption
from .base import BaseAction


class ClearHistoryAction(BaseAction):

    cmd_options = [
        CommandOption(
            template="\\clear",
            description="Clear chat",
            prefix="\\clear",
        ),
    ]

    def is_match(self, query_text: str, state: ChatState, cmd_options: list[CommandOption]) -> bool:
        matches_other_cmd = self.matches_other_cmd(query_text, state, cmd_options)
        if matches_other_cmd:
            return False
        else:
            return query_text == r"\c"

    def run(self, query_text: str, state: ChatState) -> ChatState:
        self.con.print("\n[bold green]Chat history cleared.[/bold green]")
        state.messages = []
        return state
