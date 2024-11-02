from rich.padding import Padding
from rich.markup import escape

from src.schema import ChatState, ChatMessage, Role, CommandOption
from src.web import fetch_text_for_url
from .base import BaseAction


class ReadWebAction(BaseAction):

    cmd_options = [
        CommandOption(
            template="\web <url>",
            description="Read website",
            prefix="\web",
            example="\web example.com",
        ),
    ]

    def is_match(self, query_text: str, state: ChatState, cmd_options: list[CommandOption]) -> bool:
        matches_other_cmd = self.matches_other_cmd(query_text, state, cmd_options)
        if matches_other_cmd:
            return False
        else:
            return query_text.startswith(r"\web ")

    def run(self, query_text: str, state: ChatState) -> ChatState:
        url = query_text[5:].strip()
        url_text = fetch_text_for_url(url)
        self.con.print(f"\n[bold blue]Content from {url}:[/bold blue]")
        max_char = 512
        if len(url_text) > max_char:
            url_text_display = url_text[:512] + "..."
        else:
            url_text_display = url_text

        formatted_text = Padding(escape(url_text_display), (1, 2))
        self.con.print(formatted_text)
        url_text_length = len(url_text)
        query_text = f"Content from {url} ({url_text_length} chars total):\n\n{url_text}"
        state.messages.append(ChatMessage(role=Role.User, content=query_text))
        return state
