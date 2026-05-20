from __future__ import annotations

from pydantic import BaseModel, Field


class DocumentSafeStreamRequest(BaseModel):
    """Represent a safe response request for a processed document."""

    model: str = Field(min_length=1)
    settings: dict[str, str] = Field(default_factory=dict)
