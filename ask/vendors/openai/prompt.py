from functools import cache

from openai import OpenAI


from ask.settings import load_settings


def get_chat_completion(prompt: str, model: str) -> str:
    client = get_client()
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}], model=model
    )
    return chat_completion.choices[0].message.content


@cache
def get_client():
    settings = load_settings()
    return OpenAI(api_key=settings.OPENAI_API_KEY)
