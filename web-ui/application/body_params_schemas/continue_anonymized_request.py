from __future__ import annotations

from pydantic import BaseModel, Field


class ContinueAnonymizedRequest(BaseModel):
    """Represent approved anonymized content ready for assistant processing."""

    anonymized_content: str = Field(min_length=1)
    anonymization_id: str = Field(min_length=1)
    model: str = Field(min_length=1)
