"""Request schemas used by the ai-gateway HTTP adapter."""
from __future__ import annotations

from pydantic import BaseModel, Field


class MessageRequest(BaseModel):
    """Represent one incoming chat message.

    Attributes:
        role (str): The sender role.
        content (str): The anonymized message content.
    """

    role: str = Field(min_length=1)
    content: str = Field(min_length=1)


class ChatRequest(BaseModel):
    """Represent one ai-gateway chat handling request.

    Attributes:
        messages (list[MessageRequest]): The normalized conversation history.
        model (str): The provider model identifier.
    """

    messages: list[MessageRequest]
    model: str = Field(min_length=1)
