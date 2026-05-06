"""Pydantic schemas used by the orchestrator HTTP API."""
from __future__ import annotations

from pydantic import BaseModel, Field


class MessageStreamRequest(BaseModel):
    """Represent a prompt stream request from web-ui.

    Attributes:
        chat_id (str): The chat that will display the response.
        text (str): The original user prompt.
        model (str): The AI model selected by the user.
    """

    chat_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    model: str = Field(min_length=1)


class AnonymizedStreamRequest(BaseModel):
    """Represent a request that already contains anonymized text.

    Attributes:
        chat_id (str): The chat that will display the response.
        anonymized_text (str): The anonymized prompt sent to the assistant.
        anonymization_id (str): The privacy-shield session identifier.
        model (str): The AI model selected by the user.
    """

    chat_id: str = Field(min_length=1)
    anonymized_text: str = Field(min_length=1)
    anonymization_id: str = Field(min_length=1)
    model: str = Field(min_length=1)


class DocumentPreviewRequest(BaseModel):
    """Represent a document anonymization preview request.

    Attributes:
        chat_id (str): The chat that owns the document.
        document_id (str): The processed document identifier.
    """

    chat_id: str = Field(min_length=1)
    document_id: str = Field(min_length=1)
