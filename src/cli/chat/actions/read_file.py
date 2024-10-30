from rich.padding import Padding
from rich.markup import escape

from src.schema import ChatMessage, Role
from .base import BaseAction


class ReadFileAction(BaseAction):

    def get_help_text(self) -> tuple[str, str]:
        return (
            "read file",
            "\\file /etc/hosts",
        )

    def is_match(self, query_text: str) -> bool:
        return query_text.startswith(r"\file ")

    def run(self, query_text: str, messages: list[ChatMessage]) -> list[ChatMessage]:
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
            messages.append(ChatMessage(role=Role.User, content=query_text))
            return messages
        except FileNotFoundError:
            self.con.print(f"\n[bold red]Error: File '{file_path}' not found.[/bold red]")
            return messages
        except IOError:
            self.con.print(f"\n[bold red]Error: Unable to read file '{file_path}'.[/bold red]")
            return messages
