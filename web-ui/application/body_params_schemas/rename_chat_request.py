from __future__ import annotations

from pydantic import BaseModel, Field


class RenameChatRequest(BaseModel):
    """Represent the request body used to rename a chat."""

    title: str = Field(min_length=1, max_length=120)
