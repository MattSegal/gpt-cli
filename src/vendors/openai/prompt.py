from functools import cache

from openai import OpenAI


from src.settings import load_settings
from src.schema import ChatMessage, Role


def answer_query(prompt: str, model: str) -> str:
    client = get_client()
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}], model=model
    )
    return chat_completion.choices[0].message.content


def chat(messages: list[ChatMessage], model: str) -> ChatMessage:
    client = get_client()
    chat_completion = client.chat.completions.create(
        messages=[m.model_dump() for m in messages],
        model=model,
    )
    content = chat_completion.choices[0].message.content
    return ChatMessage(role=Role.Asssistant, content=content)


@cache
def get_client():
    settings = load_settings()
    return OpenAI(api_key=settings.OPENAI_API_KEY)
