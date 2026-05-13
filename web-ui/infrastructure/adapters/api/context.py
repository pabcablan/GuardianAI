"""Shared API context and factories for web-ui routes."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from domain.message import Message


def make_assistant_message(
    content: str,
    anonymized_content: str | None = None,
) -> Message:
    """Create an assistant message for persistence.

    Args:
        content (str): The assistant message content.
        anonymized_content (str | None): The assistant response before
            deanonymization.

    Returns:
        Message: The assistant message.
    """
    return make_message(
        role="assistant",
        content=content,
        anonymized_content=anonymized_content,
    )


def make_message(
    role: str,
    content: str,
    anonymized_content: str | None = None,
) -> Message:
    """Create a chat message.

    Args:
        role (str): The message sender role.
        content (str): The message content.
        anonymized_content (str | None): The anonymized message content.

    Returns:
        Message: The created message.
    """
    return Message(
        message_id=generate_message_id(),
        role=role,
        content=content,
        created_at=now(),
        anonymized_content=anonymized_content,
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
