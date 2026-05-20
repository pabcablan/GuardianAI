from __future__ import annotations

from pydantic import BaseModel, Field


class CreateChatRequest(BaseModel):
    """Represent the request body used to create a chat."""

    title: str | None = Field(default=None, max_length=120)
