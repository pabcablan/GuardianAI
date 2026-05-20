"""Typed request and stream models for orchestrator response workflows."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True)
class OrchestratorChatHistoryMessage:
    """Represent one anonymized history message sent to orchestrator."""

    role: str
    content: str


@dataclass(frozen=True)
class OrchestratorDocumentResponseRequest:
    """Represent the data needed to request a document response stream."""

    chat_id: str
    document_id: str
    model: str
    settings: dict[str, str]
    replacements: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class OrchestratorMessageResponseRequest:
    """Represent the data needed to request a message response stream."""

    chat_id: str
    content: str
    model: str
    history: list[OrchestratorChatHistoryMessage]
    settings: dict[str, str]
    replacements: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class OrchestratorAnonymizationPreviewRequest:
    """Represent text that must be anonymized for user preview."""

    chat_id: str
    content: str
    model: str
    settings: dict[str, str]


@dataclass(frozen=True)
class OrchestratorDocumentAnonymizationPreviewRequest:
    """Represent a processed document that must be anonymized for preview."""

    chat_id: str
    document_id: str
    settings: dict[str, str]


@dataclass(frozen=True)
class OrchestratorAnonymizedResponseRequest:
    """Represent already anonymized text ready for assistant processing."""

    chat_id: str
    anonymized_content: str
    anonymization_id: str
    model: str
    history: list[OrchestratorChatHistoryMessage]
    replacements: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class OrchestratorAnonymizationPreview:
    """Represent anonymized text prepared for review."""

    anonymized_content: str
    anonymization_id: str
    replacement_count: int
    extraction_method: str | None = None
    original_content: str | None = None
    replacements: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class OrchestratorAnonymizedPdfPreview:
    """Represent a generated anonymized PDF preview."""

    filename: str
    content: bytes


@dataclass(frozen=True)
class OrchestratorStreamChunk:
    """Represent one safe text chunk emitted by orchestrator."""

    event: Literal["chunk"]
    content: str


@dataclass(frozen=True)
class OrchestratorAnonymizedPrompt:
    """Represent the anonymized form of the user prompt."""

    event: Literal["anonymized_prompt"]
    content: str
    replacements: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class OrchestratorAnonymizedResponse:
    """Represent the anonymized assistant response."""

    event: Literal["anonymized_response"]
    content: str


@dataclass(frozen=True)
class OrchestratorStreamCompleted:
    """Represent the successful end of an orchestrator stream."""

    event: Literal["completed"]


@dataclass(frozen=True)
class OrchestratorStreamFailed:
    """Represent an error emitted by orchestrator."""

    event: Literal["error"]
    detail: str


OrchestratorStreamEvent = (
    OrchestratorStreamChunk
    | OrchestratorAnonymizedPrompt
    | OrchestratorAnonymizedResponse
    | OrchestratorStreamCompleted
    | OrchestratorStreamFailed
)
