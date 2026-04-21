from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


MessageRole = Literal["user", "assistant"]
VALID_MESSAGE_ROLES: set[MessageRole] = {"user", "assistant"}


@dataclass(frozen=True)
class Message:
    message_id: str
    role: MessageRole
    content: str
    created_at: str

    def __post_init__(self) -> None:
        if self.role not in VALID_MESSAGE_ROLES:
            raise ValueError(f"Unsupported message role: {self.role}")
        if not self.content.strip():
            raise ValueError("Message content cannot be empty.")
        if not self.created_at.strip():
            raise ValueError("Message timestamp cannot be empty.")
