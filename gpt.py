import os
import sys

import openai
from rich import print
from rich.padding import Padding
from rich.progress import Progress

openai.api_key = os.environ.get("OPENAI_KEY")


def main(prompt: str):
    if not prompt:
        print("No prompt provided")
        return

    with Progress(transient=True) as progress:
        progress.add_task("[red]Asking GPT-4...", start=False, total=None)
        result = openai.ChatCompletion.create(
            model="gpt-4", messages=[{"role": "user", "content": prompt}]
        )

    answer_text = result["choices"][0]["message"]["content"]
    answer = Padding(answer_text, (2, 4))
    print(answer)




if __name__ == "__main__":
    prompt = " ".join(sys.argv[1:])
    main(prompt)
