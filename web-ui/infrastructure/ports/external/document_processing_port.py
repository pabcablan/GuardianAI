from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ExtractDocumentRequest:
    filename: str
    content_type: str
    content: bytes


@dataclass(frozen=True)
class ExtractDocumentProgressEvent:
    event: str
    stage: str
    current: int
    total: int
    message: str


@dataclass(frozen=True)
class ExtractDocumentCompletedEvent:
    event: str
    document_id: str
    filename: str
    extracted_text: str
    page_count: int


@dataclass(frozen=True)
class ExtractDocumentErrorEvent:
    event: str
    detail: str


DocumentExtractionEvent = (
    ExtractDocumentProgressEvent
    | ExtractDocumentCompletedEvent
    | ExtractDocumentErrorEvent
)


class DocumentProcessingPort(Protocol):
    def stream_extract_document(
        self,
        request: ExtractDocumentRequest,
    ) -> Iterator[DocumentExtractionEvent]:
        """Stream extraction progress from the document-processor module."""
