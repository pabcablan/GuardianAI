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
        created_at (str): The message timestamp.
        anonymized_content (str | None): The anonymized user text, when
            available.
        anonymization_replacements (dict[str, str] | None): The replacement
            mapping used to restore anonymized placeholders, when available.
        document_id (str | None): The processed document linked to this
            message, when the message originated from a PDF workflow.
    """

    message_id: str
    role: MessageRole
    content: str
    created_at: str
    anonymized_content: str | None = None
    anonymization_replacements: dict[str, str] | None = None
    document_id: str | None = None

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
