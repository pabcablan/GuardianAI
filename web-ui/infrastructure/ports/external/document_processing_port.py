from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ExtractDocumentRequest:
    filename: str
    content_type: str
    content: bytes


@dataclass(frozen=True)
class ExtractDocumentResponse:
    document_id: str
    filename: str
    extracted_text: str
    page_count: int


class DocumentProcessingPort(Protocol):
    def extract_document(
        self,
        request: ExtractDocumentRequest,
    ) -> ExtractDocumentResponse:
        """Send a document to the document-processor module."""
