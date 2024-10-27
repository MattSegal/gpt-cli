import sys
import subprocess as sp

import click
from rich import print as rich_print
from rich.padding import Padding
from rich.markup import escape
from rich.progress import Progress
from rich.console import Console
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings

from .web import fetch_text_for_url
from .settings import load_settings, CONFIG_DIR, CONFIG_FILE, load_config, save_config
from .schema import ChatMessage, Role
from . import vendors

console = Console(width=100)


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
            # Test if the command parses
            return super(DefaultCommandGroup, self).resolve_command(ctx, args)
        except click.UsageError:
            # Command did not parse, assume it is the default command
            param_args = []
            for k, v in ctx.params.items():
                if v:
                    param_args.append(f"--{k}")

            args = [self.default_command, *param_args, *args]
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


@cli.command()
@click.argument("text", nargs=-1, required=False)
def chat(text: tuple[str, ...]):
    """
    Continue chat after initial ask

    \b
    Examples:
      ask chat
      ask chat how do I flatten a list in python

    """
    settings = load_settings()

    # Initialize with stdin/argument text if provided
    query_text = " ".join(text)
    if settings.ANTHROPIC_API_KEY:
        vendor = vendors.anthropic
    elif settings.OPENAI_API_KEY:
        vendor = vendors.openai
    else:
        raise click.ClickException("Set either ANTHROPIC_API_KEY or OPENAI_API_KEY as envars")

    model_option = vendor.DEFAULT_MODEL_OPTION
    model = vendor.MODEL_OPTIONS[model_option]
    console.print(f"[green]Chatting with {vendor.MODEL_NAME} {model_option}")
    print_help()

    if query_text:
        console.print(f"\nYou:", escape(query_text), "\n")
        messages = [ChatMessage(role=Role.User, content=query_text)]
    else:
        messages = []

    while True:
        if messages:
            with Progress(transient=True) as progress:
                progress.add_task(
                    f"[red]Asking {vendor.MODEL_NAME} {model_option}...",
                    start=False,
                    total=None,
                )
                message = vendor.chat(messages, model)

            messages.append(message)
            console.print(f"Assistant:")
            formatted_text = Padding(escape(message.content), (1, 2))
            console.print(formatted_text, width=80)
            console.print("-" * console.width, style="dim")

        try:
            kb = KeyBindings()

            @kb.add("enter")
            def _(event):
                """Submit on any enter press"""
                buf = event.current_buffer
                buf.validate_and_handle()

            @kb.add("c-j")
            def _(event):
                """Insert a newline character on Ctrl+J"""
                event.current_buffer.insert_text("\n")

            query_text = ""
            while not query_text:
                session = PromptSession(key_bindings=kb)
                query_text = session.prompt("\nYou: ", multiline=True, key_bindings=kb)
                query_text = query_text.strip()

                if query_text.startswith(r"\web "):
                    url = query_text[5:].strip()
                    url_text = fetch_text_for_url(url)
                    console.print(f"\n[bold blue]Content from {url}:[/bold blue]")
                    formatted_text = Padding(escape(url_text), (1, 2))
                    console.print(formatted_text)
                    query_text = f"Content from {url}:\n\n{url_text}"
                    messages.append(ChatMessage(role=Role.User, content=query_text))
                    query_text = ""
                    continue

                if query_text == r"\c":
                    messages = []
                    console.print("\n[bold green]Chat history cleared.[/bold green]")
                    query_text = ""
                    continue

                if query_text == r"\h":
                    print_help()
                    query_text = ""
                    continue
                if query_text == r"\q":
                    console.print("\n\nAssistant: Bye 👋")
                    return

            messages.append(ChatMessage(role=Role.User, content=query_text))

        except (KeyboardInterrupt, click.exceptions.Abort):
            console.print("\n\nAssistant: Bye 👋")
            return


HELP_OPTIONS = {
    "quit": "CTRL-C or \q",
    "clear chat": "\c",
    "newline": "CTRL-J",
    "fetch web text": "\web example.com",
    "help": "\h",
}


def print_help():
    max_key_length = max(len(key) for key in HELP_OPTIONS)
    help_text = [
        f"[green]{key.ljust(max_key_length)}:  {value}" for key, value in HELP_OPTIONS.items()
    ]
    formatted_text = Padding("\n".join(help_text), (1, 2))
    console.print(formatted_text)


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
        "DALL-E image url opener command such as (eg. `google-chrome`) (press Enter to skip)",
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

    save_config(config)  #
