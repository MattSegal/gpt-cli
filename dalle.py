import os
import sys

from rich import print
from rich.progress import Progress
from openai import OpenAI


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
