"""Value object that represents one normalized provider message."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .anonymized_text import AnonymizedText


class Role(Enum):
    """Supported roles for provider-facing conversation messages."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass(frozen=True)
class Message:
    """Represent one provider-facing message.

    Attributes:
        role (Role): The sender role.
        content (AnonymizedText): The anonymized text content.
    """

    role: Role
    content: AnonymizedText

    def to_dict(self) -> dict[str, str]:
        """Return a JSON-serializable representation of the message.

        Returns:
            dict[str, str]: The serialized message payload.
        """
        return {
            "role": self.role.value,
            "content": str(self.content),
        }
