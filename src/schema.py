import enum
from pydantic import BaseModel


class ChatMode(str, enum.Enum):
    Chat = "chat"
    Shell = "shell"
    Ssh = "ssh"


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
