from __future__ import annotations

from pydantic import BaseModel, Field


class StreamMessageRequest(BaseModel):
    """Represent the request body used to stream a message response."""

    content: str = Field(min_length=1)
    model: str = Field(min_length=1)
    settings: dict[str, str] = Field(default_factory=dict)
