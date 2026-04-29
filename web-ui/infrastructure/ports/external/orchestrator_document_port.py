"""Port for sending document uploads through orchestrator."""
from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ProcessDocumentRequest:
    """Represent a document processing request.

    Attributes:
        filename (str): The document filename.
        content_type (str): The document MIME type.
        content (bytes): The document bytes.
    """

    filename: str
    content_type: str
    content: bytes


@dataclass(frozen=True)
class ProcessDocumentProgressEvent:
    """Represent a progress event emitted during document processing.

    Attributes:
        event (str): The event type.
        stage (str): The current processing stage.
        current (int): The current progress value.
        total (int): The total progress value.
        message (str): A human-readable progress message.
    """

    event: str
    stage: str
    current: int
    total: int
    message: str


@dataclass(frozen=True)
class ProcessDocumentCompletedEvent:
    """Represent a successful document processing event.

    Attributes:
        event (str): The event type.
        document_id (str): The processed document identifier.
        filename (str): The processed document filename.
        extracted_text (str): The text extracted from the document.
        page_count (int): The number of processed pages.
    """

    event: str
    document_id: str
    filename: str
    extracted_text: str
    page_count: int


@dataclass(frozen=True)
class ProcessDocumentErrorEvent:
    """Represent a document processing error event.

    Attributes:
        event (str): The event type.
        detail (str): The error detail.
    """

    event: str
    detail: str


OrchestratorDocumentEvent = (
    ProcessDocumentProgressEvent
    | ProcessDocumentCompletedEvent
    | ProcessDocumentErrorEvent
)


class OrchestratorDocumentPort(Protocol):
    """Define document processing operations exposed by orchestrator."""

    def stream_process_document(
        self,
        request: ProcessDocumentRequest,
    ) -> Iterator[OrchestratorDocumentEvent]:
        """Stream document processing events.

        Args:
            request (ProcessDocumentRequest): The document processing request.

        Returns:
            Iterator[OrchestratorDocumentEvent]: Processing progress, completion,
            or error events.
        """
