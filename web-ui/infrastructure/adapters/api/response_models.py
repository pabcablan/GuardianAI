"""Pydantic response models used by the web-ui HTTP API."""
from __future__ import annotations

from pydantic import BaseModel
from typing import Literal


class CreateChatResponse(BaseModel):
    """Represent the response returned after creating a chat."""

    chat_id: str
    title: str


class ChatSummaryResponse(BaseModel):
    """Represent a chat summary returned by the API."""

    chat_id: str
    title: str
    last_message_preview: str
    updated_at: str


class ChatMessageResponse(BaseModel):
    """Represent a chat message returned by the API."""

    message_id: str
    role: str
    content: str
    anonymized_content: str | None = None
    created_at: str


class ChatDetailResponse(BaseModel):
    """Represent a complete chat and its message history."""

    chat_id: str
    title: str
    messages: list[ChatMessageResponse]


class AnonymizedPreviewResponse(BaseModel):
    """Represent anonymized content prepared for user approval."""

    message_id: str
    anonymized_content: str
    anonymization_id: str
    replacement_count: int
    extraction_method: str | None = None
    original_content: str | None = None


class AttachDocumentProgressResponse(BaseModel):
    """Represent a document attachment progress response."""

    event: Literal["progress"] = "progress"
    stage: str
    current: int
    total: int
    message: str


class AttachDocumentCompletedResponse(BaseModel):
    """Represent a successful document attachment response."""

    event: Literal["completed"] = "completed"
    document_id: str
    filename: str


class AttachDocumentErrorResponse(BaseModel):
    """Represent a failed document attachment response."""

    event: Literal["error"] = "error"
    detail: str


class SafeStreamChunkResponse(BaseModel):
    """Represent one safe response chunk sent to the frontend."""

    event: Literal["chunk"] = "chunk"
    content: str


class SafeStreamAnonymizedPromptResponse(BaseModel):
    """Represent the anonymized user prompt sent to the frontend."""

    event: Literal["anonymized_prompt"] = "anonymized_prompt"
    content: str


class SafeStreamCompletedResponse(BaseModel):
    """Represent a successful safe response stream completion."""

    event: Literal["completed"] = "completed"


class SafeStreamErrorResponse(BaseModel):
    """Represent a safe response stream error."""

    event: Literal["error"] = "error"
    detail: str
