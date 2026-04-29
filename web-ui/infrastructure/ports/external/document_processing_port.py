"""Port definitions for integrating web-ui with the document processor."""
from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ExtractDocumentRequest:
    """Represent a document extraction request.

    Attributes:
        filename (str): The document filename.
        content_type (str): The document MIME type.
        content (bytes): The document bytes.
    """

    filename: str
    content_type: str
    content: bytes


@dataclass(frozen=True)
class ExtractDocumentProgressEvent:
    """Represent a progress event emitted during document extraction.

    Attributes:
        event (str): The event type.
        stage (str): The current extraction stage.
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
class ExtractDocumentCompletedEvent:
    """Represent a successful document extraction event.

    Attributes:
        event (str): The event type.
        document_id (str): The extracted document identifier.
        filename (str): The extracted document filename.
        extracted_text (str): The text extracted from the document.
        page_count (int): The number of processed pages.
    """

    event: str
    document_id: str
    filename: str
    extracted_text: str
    page_count: int


@dataclass(frozen=True)
class ExtractDocumentErrorEvent:
    """Represent a document extraction error event.

    Attributes:
        event (str): The event type.
        detail (str): The error detail.
    """

    event: str
    detail: str


DocumentExtractionEvent = (
    ExtractDocumentProgressEvent
    | ExtractDocumentCompletedEvent
    | ExtractDocumentErrorEvent
)


class DocumentProcessingPort(Protocol):
    """Define the document processing operations required by web-ui."""

    def stream_extract_document(
        self,
        request: ExtractDocumentRequest,
    ) -> Iterator[DocumentExtractionEvent]:
        """Stream document extraction events.

        Args:
            request (ExtractDocumentRequest): The document extraction request.

        Returns:
            Iterator[DocumentExtractionEvent]: The extraction progress,
            completion, or error events.
        """
