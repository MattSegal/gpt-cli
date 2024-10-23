from functools import cache

from openai import OpenAI


from gpt.settings import OPENAI_API_KEY


def get_chat_completion(prompt: str, model: str) -> str:
    client = get_client()
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}], model=model
    )
    return chat_completion.choices[0].message.content


@cache
def get_client():
    return OpenAI(api_key=OPENAI_API_KEY)
