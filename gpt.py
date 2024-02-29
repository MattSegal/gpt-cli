import os
import sys

from rich import print
from rich.padding import Padding
from rich.progress import Progress
from openai import OpenAI


client = OpenAI(api_key=os.environ.get("OPENAI_KEY"))


def main(prompt: str):
    if not prompt:
        print("No prompt provided")
        return

    with Progress(transient=True) as progress:
        progress.add_task("[red]Asking GPT-4...", start=False, total=None)

        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}], model="gpt-4"
        )

    answer_text = chat_completion.choices[0].message.content
    answer = Padding(answer_text, (2, 4))
    print(answer)


if __name__ == "__main__":
    prompt = " ".join(sys.argv[1:])
    main(prompt)
