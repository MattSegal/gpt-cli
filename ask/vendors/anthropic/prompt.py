from functools import cache

import anthropic

from ask.settings import load_settings


def get_chat_completion(prompt: str, model: str) -> str:
    client = get_client()
    try:
        message = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text
    except anthropic.InternalServerError as e:
        return "Request failed - Anthropic is broken"


@cache
def get_client():
    settings = load_settings()
    return anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
