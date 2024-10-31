import enum
from pydantic import BaseModel


class ChatMode(str, enum.Enum):
    Chat = "chat"
    Shell = "shell"


class Role(str, enum.Enum):
    User = "user"
    Asssistant = "assistant"
    System = "system"


class ChatMessage(BaseModel):
    role: Role
    content: str


class ChatState(BaseModel):
    messages: list[ChatMessage]
    mode: ChatMode
