"""Typed document request and stream event models for orchestrator."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProcessDocumentRequest:
    """Represent a document processing request."""

    filename: str
    content_type: str
    content: bytes
    prompt: str = ""


@dataclass(frozen=True)
class ProcessDocumentProgressEvent:
    """Represent a progress event emitted during document processing."""

    event: str
    stage: str
    current: int
    total: int
    message: str


@dataclass(frozen=True)
class ProcessDocumentCompletedEvent:
    """Represent a successful document processing event."""

    event: str
    document_id: str
    filename: str
    extracted_text: str
    page_count: int


@dataclass(frozen=True)
class ProcessDocumentErrorEvent:
    """Represent a document processing error event."""

    event: str
    detail: str


OrchestratorDocumentEvent = (
    ProcessDocumentProgressEvent
    | ProcessDocumentCompletedEvent
    | ProcessDocumentErrorEvent
)
