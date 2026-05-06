"""Port for consuming safe response streams from orchestrator."""
from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Literal, Protocol


@dataclass(frozen=True)
class OrchestratorDocumentResponseRequest:
    """Represent the data needed to request a document response stream.

    Attributes:
        chat_id (str): The chat that will display the response stream.
        document_id (str): The processed document associated with the stream.
        model (str): The AI model selected by the user.
    """

    chat_id: str
    document_id: str
    model: str


@dataclass(frozen=True)
class OrchestratorMessageResponseRequest:
    """Represent the data needed to request a message response stream.

    Web-ui sends the original user prompt to orchestrator. Orchestrator owns the
    complete workflow with privacy-shield, the assistant API, and document
    processing.

    Attributes:
        chat_id (str): The chat that will display the response stream.
        content (str): The original user prompt.
        model (str): The AI model selected by the user.
    """

    chat_id: str
    content: str
    model: str


@dataclass(frozen=True)
class OrchestratorAnonymizationPreviewRequest:
    """Represent text that must be anonymized for user preview.

    Attributes:
        chat_id (str): The chat that owns the text.
        content (str): The text to anonymize.
        model (str): The AI model selected by the user.
    """

    chat_id: str
    content: str
    model: str


@dataclass(frozen=True)
class OrchestratorDocumentAnonymizationPreviewRequest:
    """Represent a processed document that must be anonymized for preview.

    Attributes:
        chat_id (str): The chat that owns the document.
        document_id (str): The processed document identifier.
    """

    chat_id: str
    document_id: str


@dataclass(frozen=True)
class OrchestratorAnonymizedResponseRequest:
    """Represent already anonymized text ready for assistant processing.

    Attributes:
        chat_id (str): The chat that owns the request.
        anonymized_content (str): The anonymized text.
        anonymization_id (str): The privacy-shield session identifier.
        model (str): The AI model selected by the user.
    """

    chat_id: str
    anonymized_content: str
    anonymization_id: str
    model: str


@dataclass(frozen=True)
class OrchestratorAnonymizationPreview:
    """Represent anonymized text prepared for review.

    Attributes:
        anonymized_content (str): The anonymized text.
        anonymization_id (str): The privacy-shield session identifier.
        replacement_count (int): The number of replacements found.
    """

    anonymized_content: str
    anonymization_id: str
    replacement_count: int


@dataclass(frozen=True)
class OrchestratorStreamChunk:
    """Represent one safe text chunk emitted by orchestrator.

    Attributes:
        event (Literal["chunk"]): The stream event type.
        content (str): The response chunk safe for UI rendering.
    """

    event: Literal["chunk"]
    content: str


@dataclass(frozen=True)
class OrchestratorAnonymizedPrompt:
    """Represent the anonymized form of the user prompt.

    Attributes:
        event (Literal["anonymized_prompt"]): The stream event type.
        content (str): The prompt after anonymization.
    """

    event: Literal["anonymized_prompt"]
    content: str


@dataclass(frozen=True)
class OrchestratorStreamCompleted:
    """Represent the successful end of an orchestrator stream.

    Attributes:
        event (Literal["completed"]): The stream event type.
    """

    event: Literal["completed"]


@dataclass(frozen=True)
class OrchestratorStreamFailed:
    """Represent an error emitted by orchestrator.

    Attributes:
        event (Literal["error"]): The stream event type.
        detail (str): The error detail.
    """

    event: Literal["error"]
    detail: str


OrchestratorStreamEvent = (
    OrchestratorStreamChunk
    | OrchestratorAnonymizedPrompt
    | OrchestratorStreamCompleted
    | OrchestratorStreamFailed
)


class OrchestratorResponsePort(Protocol):
    """Define how web-ui consumes safe streams from orchestrator."""

    def preview_message_anonymization(
        self,
        request: OrchestratorAnonymizationPreviewRequest,
    ) -> OrchestratorAnonymizationPreview:
        """Return anonymized text without calling the assistant.

        Args:
            request (OrchestratorAnonymizationPreviewRequest): The text to
                anonymize.

        Returns:
            OrchestratorAnonymizationPreview: The anonymized text metadata.
        """

    def preview_document_anonymization(
        self,
        request: OrchestratorDocumentAnonymizationPreviewRequest,
    ) -> OrchestratorAnonymizationPreview:
        """Return an anonymized processed document without calling the assistant.

        Args:
            request (OrchestratorDocumentAnonymizationPreviewRequest): The
                processed document identifiers.

        Returns:
            OrchestratorAnonymizationPreview: The anonymized text metadata.
        """

    def stream_anonymized_response(
        self,
        request: OrchestratorAnonymizedResponseRequest,
    ) -> Iterator[OrchestratorStreamEvent]:
        """Stream a response from already anonymized text.

        Args:
            request (OrchestratorAnonymizedResponseRequest): The anonymized
                text and session identifier.

        Returns:
            Iterator[OrchestratorStreamEvent]: Safe text chunks and terminal
            stream events emitted by orchestrator.
        """

    def stream_safe_response(
        self,
        request: OrchestratorDocumentResponseRequest,
    ) -> Iterator[OrchestratorStreamEvent]:
        """Stream safe response events for a processed document.

        Args:
            request (OrchestratorDocumentResponseRequest): The chat and processed
            document identifiers needed to locate the stream.

        Returns:
            Iterator[OrchestratorStreamEvent]: Safe text chunks and terminal
            stream events emitted by orchestrator.
        """

    def stream_message_response(
        self,
        request: OrchestratorMessageResponseRequest,
    ) -> Iterator[OrchestratorStreamEvent]:
        """Stream a safe assistant response for a user chat message.

        Args:
            request (OrchestratorMessageResponseRequest): The chat identifier and
            original user prompt.

        Returns:
            Iterator[OrchestratorStreamEvent]: Safe text chunks and terminal
            stream events emitted by orchestrator.
        """
