import subprocess as sp

import click
from rich.progress import Progress
from rich.console import Console

from src.settings import load_settings
from src import vendors
from .cli import cli


@cli.command()
@click.argument("text", nargs=-1, required=True)
def img(text: tuple[str, ...]):
    """
    Render an image with DALLE-3

    \b
    ask img the best hamburger ever
    ask img a skier doing a backflip high quality photorealistic
    ask img an oil painting of the best restaurant in melbourne
    """
    prompt = " ".join(text)
    if not prompt:
        print("No prompt provided")
        raise click.ClickException("No prompt provided")

    settings = load_settings()
    if not settings.OPENAI_API_KEY:
        raise click.ClickException("Set the OPENAI_API_KEY envar")

    if not settings.DALLE_IMAGE_OPENER:
        raise click.ClickException("Set the DALLE_IMAGE_OPENER envar")

    with Progress(transient=True) as progress:
        progress.add_task("[red]Asking DALL-E...", start=False, total=None)
        image_url = vendors.openai.get_image_url(prompt)

    # Open the image URL using the configured opener command
    opener_cmd = settings.DALLE_IMAGE_OPENER.replace("\\", "")
    sp.run([opener_cmd, image_url])
