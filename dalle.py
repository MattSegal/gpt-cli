import sys
import os

from openai import OpenAI
from rich.progress import Progress


OPENAI_KEY_EXISTS = os.getenv("OPENAI_API_KEY") or False
if not OPENAI_KEY_EXISTS:
    print("No API key found: please set OPENAI_API_KEY to use DALL-E")
    sys.exit(1)


client = OpenAI()


def main(filename: str, prompt: str):
    if not filename:
        print("No output filename provided")
        return

    if not prompt:
        print("No prompt provided")
        return

    with Progress(transient=True) as progress:
        progress.add_task("[red]Asking DALL-E...", start=False, total=None)
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            style="vivid",
            size="1792x1024",
            quality="hd",
            n=1,
        )

    image_url = response.data[0].url
    with open(filename, "w") as f:
        f.write(image_url)


if __name__ == "__main__":
    filename = sys.argv[1]
    prompt = sys.argv[2]
    main(filename, prompt)
