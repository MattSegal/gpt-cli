import sys

from rich import print as rich_print
from rich.padding import Padding
from rich.markup import escape
from rich.progress import Progress
import click

from .app import ChatApp
from .web import fetch_text_for_url
from .settings import OPENAI_API_KEY, ANTHROPIC_API_KEY
from . import vendors


@click.group()
def cli():
    """CLI tool for web scraping and AI chat"""
    pass


@cli.command()
@click.argument("urls", nargs=-1)
@click.option(
    "--pretty", is_flag=True, default=False, help="Use rich text formatting for output"
)
def scrape(urls, pretty):
    """Scrape content from provided URLs"""
    for url in urls:
        url_text = fetch_text_for_url(url)
        if pretty:
            rich_print(f"\n[bold blue]Content from {url}:[/bold blue]")
            formatted_text = Padding(escape(url_text), (1, 2))
            rich_print(formatted_text)
        else:
            print(f"\nContent from {url}:")
            print(url_text)


@cli.command()
@click.argument("text", nargs=-1, required=False)
@click.option("--chat", is_flag=True, default=False, help="Use chat UI")
def chat(text: tuple[str, ...], chat: bool):
    """
    Ask GPT or Claude a question. Examples:

    \b
    gpt how do I flatten a list in python
    gpt ffmpeg convert webm to a gif
    gpt what is the best restaurant in melbourne
    echo 'hello world' | gpt what does this text say
    gpt --nano # Incompatible with pipes
    gpt --chat # Incompatible with pipes
    """

    # Initialize with stdin/argument text if provided
    query_text = " ".join(text)
    if not chat and not sys.stdin.isatty():
        stdin_text = click.get_text_stream("stdin").read()
        query_text = f"{query_text}\n{stdin_text}" if query_text else stdin_text

    # Add this condition to print help when no input is provided
    if not query_text and not chat:
        ctx = click.get_current_context()
        click.echo(ctx.get_help())
        ctx.exit()

    if chat:
        app = ChatApp(query_text)
        app.run()
    else:
        if ANTHROPIC_API_KEY:
            vendor = vendors.anthropic
        elif OPENAI_API_KEY:
            vendor = vendors.openai
        else:
            print("Set either ANTHROPIC_API_KEY or OPENAI_API_KEY as envars")
            sys.exit(1)

        model_option = vendor.DEFAULT_MODEL_OPTION
        model = vendor.MODEL_OPTIONS[model_option]
        with Progress(transient=True) as progress:
            progress.add_task(
                f"[red]Asking {vendor.MODEL_NAME} {model_option}...",
                start=False,
                total=None,
            )
            answer_text = vendor.get_chat_completion(query_text, model)

        formatted_text = Padding(escape(answer_text), (1, 2))
        rich_print(formatted_text)


@cli.command()
@click.argument("filename", type=click.Path(writable=True), required=True)
@click.argument("text", nargs=-1, required=True)
def image(filename: str, text: tuple[str, ...]):
    prompt = " ".join(text)
    if not filename:
        print("No output filename provided")
        return

    if not prompt:
        print("No prompt provided")
        return

    if not OPENAI_API_KEY:
        print("Set the OPENAI_API_KEY envar")
        sys.exit(1)

    with Progress(transient=True) as progress:
        progress.add_task("[red]Asking DALL-E...", start=False, total=None)
        image_url = vendors.openai.get_image_url(prompt)

    with open(filename, "w") as f:
        f.write(image_url)


cli()
