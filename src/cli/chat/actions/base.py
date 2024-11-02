from rich.console import Console

from src.schema import ChatState, CommandOption


class BaseAction:

    cmd_options: list[CommandOption]

    def __init__(self, console: Console):
        self.con = console

    def matches_other_cmd(
        self, query_text: str, state: ChatState, cmd_options: list[CommandOption]
    ) -> bool:
        """
        Returns True if query matches a command option, but it's not for this action
        """
        for cmd_option in cmd_options:
            if cmd_option.prefix is None:
                continue

            matches_a_command = query_text.startswith(cmd_option.prefix)
            is_not_this_action = not any([cmd_option.prefix == o.prefix for o in self.cmd_options])
            if matches_a_command and is_not_this_action:
                return True

        return False

    def is_match(self, query_text: str, state: ChatState, cmd_options: list[CommandOption]) -> bool:
        raise NotImplementedError()

    def run(self, query_text: str, state: ChatState) -> ChatState:
        raise NotImplementedError()
