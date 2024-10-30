from dataclasses import dataclass


@dataclass
class ChatState:
    is_shell_active: bool
