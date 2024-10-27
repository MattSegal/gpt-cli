import click
from rich import print as rich_print
from rich.padding import Padding
from rich.markup import escape

from src.web import fetch_text_for_url
from .cli import cli


@cli.command()
@click.argument("urls", nargs=-1)
@click.option("--pretty", is_flag=True, default=False, help="Use rich text formatting for output")
def web(urls, pretty):
    """Scrape content from provided URLs (HTML, PDFs)"""

    for url in urls:
        url_text = fetch_text_for_url(url)

        if pretty:
            rich_print(f"\n[bold blue]Content from {url}:[/bold blue]")
            formatted_text = Padding(escape(url_text), (1, 2))
            rich_print(formatted_text)
        else:
            print(f"\nContent from {url}:")
            print(url_text)
