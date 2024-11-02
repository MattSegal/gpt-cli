from rich.padding import Padding
from rich.markup import escape

from src.schema import ChatState, ChatMessage, Role, ChatMode, CommandOption
from .base import BaseAction


class ReadFileAction(BaseAction):

    help_description = "read file"
    help_examples = ["\\file /etc/hosts"]
    active_modes = [ChatMode.Chat, ChatMode.Shell]

    cmd_options = [
        CommandOption(
            template="\\file <path>",
            description="Read file",
            prefix="\\file",
            example="\\file /etc/hosts",
        ),
    ]

    def is_match(self, query_text: str, state: ChatState, cmd_options: list[CommandOption]) -> bool:
        matches_other_cmd = self.matches_other_cmd(query_text, state, cmd_options)
        if matches_other_cmd:
            return False
        else:
            return query_text.startswith(r"\file ")

    def run(self, query_text: str, state: ChatState) -> ChatState:
        file_path = query_text[6:].strip()
        try:
            with open(file_path, "r") as file:
                file_content = file.read()
            self.con.print(f"\n[bold blue]Content from {file_path}:[/bold blue]")
            max_char = 512
            if len(file_content) > max_char:
                file_content_display = file_content[:512] + "..."
            else:
                file_content_display = file_content

            formatted_text = Padding(escape(file_content_display), (1, 2))
            self.con.print(formatted_text)
            file_content_length = len(file_content)
            query_text = (
                f"Content from {file_path} ({file_content_length} chars total):\n\n{file_content}"
            )
            state.messages.append(ChatMessage(role=Role.User, content=query_text))
            return state
        except FileNotFoundError:
            self.con.print(f"\n[bold red]Error: File '{file_path}' not found.[/bold red]")
            return state
        except IOError:
            self.con.print(f"\n[bold red]Error: Unable to read file '{file_path}'.[/bold red]")
            return state
