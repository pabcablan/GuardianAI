"""Port for requesting document extraction from document-processor."""
from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class DocumentUploadRequest:
    """Represent a document upload sent to document-processor.

    Attributes:
        filename (str): The uploaded filename.
        content_type (str): The uploaded content type.
        content (bytes): The uploaded file content.
    """

    filename: str
    content_type: str
    content: bytes


class DocumentProcessorPort(Protocol):
    """Define how orchestrator requests document extraction."""

    def stream_extract_document(
        self,
        request: DocumentUploadRequest,
    ) -> Iterator[dict[str, Any]]:
        """Send a document and stream extraction events.

        Args:
            request (DocumentUploadRequest): The document upload request.

        Returns:
            Iterator[dict[str, Any]]: Document extraction events.
        """
