import enum
from typing import Any
from pydantic import BaseModel


class ChatMode(str, enum.Enum):
    Chat = "chat"
    Shell = "shell"
    Ssh = "ssh"
    Task = "task"


class Role(str, enum.Enum):
    User = "user"
    Asssistant = "assistant"
    System = "system"


class ChatMessage(BaseModel):
    role: Role
    content: str


class SshConfig(BaseModel):
    host: str
    username: str
    port: int = 22

    @property
    def conn_name(self) -> str:
        return f"{self.username}@{self.host}"


class ChatState(BaseModel):
    messages: list[ChatMessage]
    mode: ChatMode
    ssh_config: SshConfig | None


class CommandOption(BaseModel):
    template: str
    description: str
    prefix: str | None = None
    example: str | None = None


class TaskMeta(BaseModel):
    name: str
    description: str
    summary: str
    slug: str
    input_schema: dict
    output_schema: dict
    depends_on: list[str]


class TaskTool(BaseModel):
    function: Any
    name: str
    description: str
    input_schema: dict
    output_schema: dict

    def to_schema(self):
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
        }
