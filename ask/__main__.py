import sys

from rich import print as rich_print
from rich.padding import Padding
from rich.markup import escape
from rich.progress import Progress
import click

from .app import ChatApp
from .web import fetch_text_for_url
from .settings import load_settings, CONFIG_DIR, CONFIG_FILE, load_config, save_config
from . import vendors


class DefaultCommandGroup(click.Group):
    """allow a default command for a group"""

    def command(self, *args, **kwargs):
        default_command = kwargs.pop("default_command", False)
        if default_command and not args:
            kwargs["name"] = kwargs.get("name", "<default>")
        decorator = super(DefaultCommandGroup, self).command(*args, **kwargs)

        if default_command:

            def new_decorator(f):
                cmd = decorator(f)
                self.default_command = cmd.name
                return cmd

            return new_decorator

        return decorator

    def resolve_command(self, ctx, args):
        try:
            # test if the command parses
            return super(DefaultCommandGroup, self).resolve_command(ctx, args)
        except click.UsageError:
            # command did not parse, assume it is the default command
            args.insert(0, self.default_command)
            return super(DefaultCommandGroup, self).resolve_command(ctx, args)


@click.group(cls=DefaultCommandGroup)
def cli():
    """
    Ask your language model a question.

    \b
    Examples:
      ask how do I flatten a list in python
      ask ffmpeg convert webm to a gif
      ask what is the best restaurant in melbourne
      echo 'hello world' | ask what does this text say
      ask web http://example.com | ask what does this website say

    """

    pass


@cli.command(default_command=True)
@click.argument("text", nargs=-1, required=False)
@click.pass_context
def ask(ctx, text: tuple[str, ...]):
    """
    Simple one-off queries with no chat history
    """
    if ctx.invoked_subcommand is not None:
        return

    settings = load_settings()

    # Initialize with stdin/argument text if provided
    query_text = " ".join(text)
    if not sys.stdin.isatty():
        stdin_text = click.get_text_stream("stdin").read()
        query_text = f"{query_text}\n{stdin_text}" if query_text else stdin_text

    # Add this condition to print help when no input is provided
    if not query_text:
        ctx = click.get_current_context()
        click.echo(ctx.get_help())
        ctx.exit()

    if settings.ANTHROPIC_API_KEY:
        vendor = vendors.anthropic
    elif settings.OPENAI_API_KEY:
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


@cli.command()
@click.argument("text", nargs=-1, required=False)
def ui(text: tuple[str, ...]):
    """Chat via a terminal UI"""
    # Initialize with stdin/argument text if provided
    query_text = " ".join(text)
    app = ChatApp(query_text)
    app.run()


@cli.command()
@click.argument("filename", type=click.Path(writable=True), required=True)
@click.argument("text", nargs=-1, required=True)
def img(filename: str, text: tuple[str, ...]):
    """
    Render an image with Dalle-3
    """
    prompt = " ".join(text)
    if not filename:
        print("No output filename provided")
        return

    if not prompt:
        print("No prompt provided")
        return

    settings = load_settings()
    if not settings.OPENAI_API_KEY:
        print("Set the OPENAI_API_KEY envar")
        sys.exit(1)

    with Progress(transient=True) as progress:
        progress.add_task("[red]Asking DALL-E...", start=False, total=None)
        image_url = vendors.openai.get_image_url(prompt)

    with open(filename, "w") as f:
        f.write(image_url)


@cli.command()
@click.option("--list", "show_list", is_flag=True, default=False, help="Print current settings")
def config(show_list: bool):
    """
    Set up or configure this tool
    """
    CONFIG_DIR.mkdir(exist_ok=True)
    config = load_config()

    if show_list:
        rich_print(f"\n[bold]Config at {CONFIG_FILE}:[/bold]\n")
        for key, value in config.items():
            if key.endswith("_KEY"):  # Only mask API keys
                value_len = len(value)
                visible_len = value_len // 2
                masked_value = value[:visible_len] + "*" * (value_len - visible_len)
                rich_print(f"  {key}: {masked_value}")
            else:
                rich_print(f"  {key}: {value}")

        return

    openai_key = click.prompt(
        "OpenAI API Key (press Enter to skip)",
        default=config.get("OPENAI_API_KEY", ""),
        show_default=False,
        type=str,
    )
    anthropic_key = click.prompt(
        "Anthropic API Key (press Enter to skip)",
        default=config.get("ANTHROPIC_API_KEY", ""),
        show_default=False,
        type=str,
    )
    dalle_opener = click.prompt(
        "DALL-E image url opener command (press Enter to skip)",
        default=config.get("DALLE_IMAGE_OPENER", ""),
        show_default=False,
        type=str,
    )

    # Update config with new values, removing empty ones
    if openai_key:
        config["OPENAI_API_KEY"] = openai_key
    if anthropic_key:
        config["ANTHROPIC_API_KEY"] = anthropic_key
    if dalle_opener:
        config["DALLE_IMAGE_OPENER"] = dalle_opener

    save_config(config)


if __name__ == "__main__":
    cli()
