from rich.markup import escape
from textual.app import App, ComposeResult
from textual.containers import ScrollableContainer
from textual.widgets import Header, Footer, TextArea, RichLog
from textual.binding import Binding

from .settings import load_settings
from . import vendors


class ChatApp(App):
    CSS = """
    Screen {
        align: center middle;
    }

    #chat-container {
        width: 100%;
        height: 1fr;
        border: solid green;
    }

    #message-input {
        width: 100%;
        height: 20%;
        dock: bottom;
        border: solid blue;
    }

    #chat-history {
        width: 100%;
        height: 80%;
        overflow-y: scroll;
        border: solid red;
    }
    """

    BINDINGS = [
        Binding("ctrl+c,ctrl+q", "quit", "Quit", show=True),
        Binding("ctrl+s", "submit", "Submit", show=True),
    ]

    def __init__(self, initial_text: str = ""):
        super().__init__()
        self.initial_text = initial_text
        self.settings = load_settings()

    def compose(self) -> ComposeResult:
        yield Header()
        with ScrollableContainer(id="chat-container"):
            yield RichLog(id="chat-history", highlight=True, markup=True)
            yield TextArea(self.initial_text, id="message-input")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#message-input").focus()

    async def action_submit(self) -> None:
        input_widget = self.query_one("#message-input")
        message = input_widget.text

        if not message.strip():
            return

        # Add user message to chat
        history = self.query_one("#chat-history")
        history.write(f"[bold]You:[/bold] {escape(message)}")

        # Get AI response
        if self.settings.ANTHROPIC_API_KEY:
            vendor = vendors.anthropic
        elif self.settings.OPENAI_API_KEY:
            vendor = vendors.openai
        else:
            history.write("Error: Set either ANTHROPIC_API_KEY or OPENAI_API_KEY as envars")
            return

        # Show thinking indicator
        history.write("[bold red]Thinking...[/bold red]")

        # Get response from AI
        model_option = vendor.DEFAULT_MODEL_OPTION
        model = vendor.MODEL_OPTIONS[model_option]
        answer_text = vendor.get_chat_completion(message, model)

        # Remove last line (thinking indicator) and show response
        history.lines.pop()
        history.write(f"[bold]Assistant:[/bold] {answer_text}")

        # Clear input
        input_widget.text = ""
