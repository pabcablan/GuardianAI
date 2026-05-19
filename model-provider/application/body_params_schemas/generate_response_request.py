"""Request schema for model text generation."""
from __future__ import annotations

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    """Represent one inference request sent to model-provider.

    Attributes:
        model_name (str): The runtime name of the loaded model.
        system_prompt (str | None): Optional system instructions.
        prompt (str): The user prompt or extraction instruction.
        document_base64 (str | None): Optional base64-encoded PDF payload.
    """

    model_name: str = Field(min_length=1)
    system_prompt: str | None = None
    prompt: str = Field(min_length=1)
    document_base64: str | None = None
