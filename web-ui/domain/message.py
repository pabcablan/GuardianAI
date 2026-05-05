"""Domain model for messages exchanged in a conversation."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


MessageRole = Literal["user", "assistant"]
VALID_MESSAGE_ROLES: set[MessageRole] = {"user", "assistant"}


@dataclass(frozen=True)
class Message:
    """Represent one message emitted by the user or assistant.

    Attributes:
        message_id (str): The message identifier.
        role (MessageRole): The sender role.
    content (str): The message text.
    anonymized_content (str | None): The anonymized user text, when available.
    created_at (str): The message timestamp.
    """

    message_id: str
    role: MessageRole
    content: str
    created_at: str
    anonymized_content: str | None = None

    def __post_init__(self) -> None:
        """Validate the message fields.

        Raises:
            ValueError: If the role is unsupported, the content is empty, or
            the timestamp is empty.
        """
        if self.role not in VALID_MESSAGE_ROLES:
            raise ValueError(f"Unsupported message role: {self.role}")
        if not self.content.strip():
            raise ValueError("Message content cannot be empty.")
        if not self.created_at.strip():
            raise ValueError("Message timestamp cannot be empty.")
