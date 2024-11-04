import json
import os
from pathlib import Path
from functools import cache

from rich import print as rich_print
from pydantic import Field
from pydantic_settings import BaseSettings


CONFIG_DIR = Path.home() / ".ask"
CONFIG_FILE = CONFIG_DIR / "config.json"
TASKS_DIR = CONFIG_DIR / "tasks"


@cache
def load_settings():
    return Settings()


@cache
def load_config() -> dict:
    if not CONFIG_FILE.exists():
        return {}

    try:
        with open(CONFIG_FILE) as f:
            return json.load(f)
    except json.JSONDecodeError:
        rich_print("[red]Error: Invalid config file format[/red]")
        return {}


def save_config(config: dict):
    # Ensure config directory exists
    CONFIG_DIR.mkdir(exist_ok=True)

    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
        rich_print("[green]Configuration saved to[/green]", CONFIG_FILE)
    except Exception as e:
        rich_print("[red]Error saving configuration:[/red]", str(e))


# https://docs.pydantic.dev/latest/concepts/pydantic_settings/
class Settings(BaseSettings):
    OPENAI_API_KEY: str | None = Field(
        default_factory=lambda: load_config().get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    )
    ANTHROPIC_API_KEY: str | None = Field(
        default_factory=lambda: load_config().get("ANTHROPIC_API_KEY")
        or os.getenv("ANTHROPIC_API_KEY")
    )
    DALLE_IMAGE_OPENER: str | None = Field(
        default_factory=lambda: load_config().get("DALLE_IMAGE_OPENER")
    )

    def model_post_init(self, *args, **kwargs):
        super().model_post_init(*args, **kwargs)
        if not self.OPENAI_API_KEY and not self.ANTHROPIC_API_KEY:
            raise ValueError("Either OPENAI_API_KEY or ANTHROPIC_API_KEY must be set")
