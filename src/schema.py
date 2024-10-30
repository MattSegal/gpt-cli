import enum
from pydantic import BaseModel


class Role(str, enum.Enum):
    User = "user"
    Asssistant = "assistant"
    System = "system"


class ChatMessage(BaseModel):
    role: Role
    content: str


class ChatState(BaseModel):
    messages: list[ChatMessage]
    is_shell_active: bool
