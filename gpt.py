import sys
import os

import anthropic
from openai import OpenAI
from rich import print
from rich.markup import escape
from rich.padding import Padding
from rich.progress import Progress

ANTHROPIC_KEY_EXISTS = os.getenv("ANTHROPIC_API_KEY") or False
OPENAI_KEY_EXISTS = os.getenv("OPENAI_API_KEY") or False

anthropic_client, openai_client = None, None
if OPENAI_KEY_EXISTS:
    openai_client = OpenAI()

if ANTHROPIC_KEY_EXISTS:
    anthropic_client = anthropic.Anthropic()

if not (openai_client or anthropic_client):
    print("No API keys set: please set OPENAI_API_KEY or ANTHROPIC_API_KEY")
    sys.exit(1)


class ClaudeModel:
    Opus = "claude-3-opus-20240229"
    Sonnet = "claude-3-5-sonnet-20240620"
    Haiku = "claude-3-haiku-20240307"


class GPTModel:
    FourTurbo = "gpt-4-1106-preview"
    FourO = "gpt-4o"


ANTHROPIC_MODEL = ClaudeModel.Sonnet
GPT_MODEL = GPTModel.FourO

model_options = {
    "opus": ClaudeModel.Opus,
    "sonnet": ClaudeModel.Sonnet,
    "haiku": ClaudeModel.Haiku,
}


def main(prompt: str):
    if not prompt:
        print("No prompt provided")
        return

    prompt = prompt.replace("--nano", "")
    with Progress(transient=True) as progress:
        if ANTHROPIC_KEY_EXISTS:
            model = ANTHROPIC_MODEL
            model_name = "Claude 3"
            for model_key, model_id in model_options.items():
                if f"--{model_key}" in prompt:
                    model = model_id
                    model_name = f"Claude 3 ({model_key})"
                    prompt = prompt.replace(f"--{model_key}", "")
                    break

            progress.add_task(f"[red]Asking {model_name}...", start=False, total=None)
            try:
                answer_text = prompt_anthropic(prompt, model)
            except anthropic.InternalServerError as e:
                answer_text = "Request failed - Anthropic is broken"
        elif OPENAI_KEY_EXISTS:
            progress.add_task("[red]Asking GPT-4...", start=False, total=None)
            answer_text = prompt_gpt(prompt)
        else:
            raise ValueError("Set either ANTHROPIC_API_KEY or OPENAI_API_KEY as envars")

    answer = Padding(escape(answer_text), (2, 4))
    print(answer)


def prompt_anthropic(prompt: str, model: str):
    message = anthropic_client.messages.create(
        model=model,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def prompt_gpt(prompt: str):
    chat_completion = openai_client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}], model=GPT_MODEL
    )
    return chat_completion.choices[0].message.content


if __name__ == "__main__":
    prompt = " ".join(sys.argv[1:])
    if not sys.stdin.isatty():
        stdin_text = sys.stdin.read()
        prompt += "\n" + stdin_text

    main(prompt)
