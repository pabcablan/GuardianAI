"""Shared API context and factories for web-ui routes."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

from domain.message import Message


@dataclass
class WebUiApiState:
    """Hold API state that does not belong to domain entities."""

    processed_document_user_messages: dict[str, str] = field(
        default_factory=dict,
    )


def make_assistant_message(content: str) -> Message:
    """Create an assistant message for persistence.

    Args:
        content (str): The assistant message content.

    Returns:
        Message: The assistant message.
    """
    return make_message(role="assistant", content=content)


def make_message(role: str, content: str) -> Message:
    """Create a chat message.

    Args:
        role (str): The message sender role.
        content (str): The message content.

    Returns:
        Message: The created message.
    """
    return Message(
        message_id=generate_message_id(),
        role=role,
        content=content,
        created_at=now(),
    )


def generate_message_id() -> str:
    """Generate a unique message identifier.

    Returns:
        str: The generated message identifier.
    """
    return f"msg-{uuid4().hex}"


def now() -> str:
    """Return the current UTC timestamp.

    Returns:
        str: The current timestamp.
    """
    return datetime.now(timezone.utc).isoformat()
