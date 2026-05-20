from __future__ import annotations

from pydantic import BaseModel, Field


class DocumentAnonymizationRequest(BaseModel):
    """Represent anonymization preferences for a processed document."""

    settings: dict[str, str] = Field(default_factory=dict)
