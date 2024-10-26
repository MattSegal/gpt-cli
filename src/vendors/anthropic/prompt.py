from functools import cache

import anthropic

from src.settings import load_settings
from src.schema import ChatMessage, Role


def answer_query(prompt: str, model: str) -> str:
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


def chat(messages: list[ChatMessage], model: str) -> ChatMessage:
    client = get_client()
    messages = [
        ChatMessage(role=Role.User, content=m.content) if m.role == Role.System else m
        for m in messages
    ]
    try:
        message = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[m.model_dump() for m in messages],
        )
        content = message.content[0].text
    except anthropic.InternalServerError:
        content = "Request failed - Anthropic is broken"

    return ChatMessage(role=Role.Asssistant, content=content)


@cache
def get_client():
    settings = load_settings()
    return anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
