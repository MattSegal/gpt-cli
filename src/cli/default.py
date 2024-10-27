import sys

import click
from rich.padding import Padding
from rich.markup import escape
from rich.progress import Progress
from rich.console import Console

from src.settings import load_settings
from src import vendors
from .cli import cli

console = Console(width=100)


@cli.command(default_command=True)
@click.argument("text", nargs=-1, required=False)
def default(text: tuple[str, ...]):
    """
    Simple one-off queries with no chat history
    """
    settings = load_settings()

    # Initialize with stdin/argument text if provided
    query_text = " ".join(text)
    if not sys.stdin.isatty():
        stdin_text = click.get_text_stream("stdin").read()
        query_text = f"{query_text}\n{stdin_text}" if query_text else stdin_text

    if settings.ANTHROPIC_API_KEY:
        vendor = vendors.anthropic
    elif settings.OPENAI_API_KEY:
        vendor = vendors.openai
    else:
        raise click.ClickException("Set either ANTHROPIC_API_KEY or OPENAI_API_KEY as envars")

    model_option = vendor.DEFAULT_MODEL_OPTION
    model = vendor.MODEL_OPTIONS[model_option]

    # User asks a single questions
    with Progress(transient=True) as progress:
        progress.add_task(
            f"[red]Asking {vendor.MODEL_NAME} {model_option}...",
            start=False,
            total=None,
        )
        answer_text = vendor.answer_query(query_text, model)

    formatted_text = Padding(escape(answer_text), (1, 2))
    console.print(formatted_text)
