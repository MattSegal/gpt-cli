import sys

from rich import print as rich_print
from rich.padding import Padding
from rich.markup import escape
from rich.progress import Progress
import click

from .app import ChatApp
from .web import fetch_text_for_url
from .settings import OPENAI_API_KEY
from . import vendors


@click.group()
def cli():
    """CLI tool for web scraping and AI chat"""
    pass


@cli.command()
@click.argument("urls", nargs=-1)
@click.option(
    "--pretty/--no-pretty", default=False, help="Use rich text formatting for output"
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
def chat(text: tuple[str, ...]):
    # Initialize with stdin/argument text if provided
    initial_text = " ".join(text)
    if not sys.stdin.isatty():
        stdin_text = click.get_text_stream("stdin").read()
        initial_text = f"{initial_text}\n{stdin_text}" if initial_text else stdin_text

    breakpoint()
    app = ChatApp(initial_text)
    app.run()


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
