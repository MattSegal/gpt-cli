import click
from rich import print as rich_print

from src.settings import CONFIG_DIR, CONFIG_FILE, load_config, save_config
from .cli import cli


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

    save_config(config)
