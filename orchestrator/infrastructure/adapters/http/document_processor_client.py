"""HTTP client used by orchestrator to call document-processor."""
from __future__ import annotations

import json
import mimetypes
import os
import uuid
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

import httpx

from infrastructure.adapters.http.base import (
    ExternalHttpClientBase,
    ExternalServiceClientError,
)
from infrastructure.ports.document_processor_port import (
    DocumentProcessorPort,
    DocumentUploadRequest,
)


class DocumentProcessorClientError(ExternalServiceClientError):
    """Represent a document-processor communication failure."""


@dataclass(frozen=True)
class HttpDocumentProcessingClient(
    ExternalHttpClientBase,
    DocumentProcessorPort,
):
    """Call document-processor HTTP endpoints from orchestrator."""

    base_url: str = os.getenv(
        "DOCUMENT_PROCESSOR_BASE_URL",
        "http://127.0.0.1:8001",
    )

    def stream_extract_document(
        self,
        request: DocumentUploadRequest,
    ) -> Iterator[dict[str, Any]]:
        """Send a PDF to document-processor and yield extraction events.

        Args:
            request (DocumentUploadRequest): The document upload data.

        Returns:
            Iterator[dict[str, Any]]: Progress and completion events adapted
            from the document-processor response.
        """
        yield {
            "event": "progress",
            "stage": "uploading",
            "current": 1,
            "total": 3,
            "message": "Sending document to document processor...",
        }

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(
                    f"{self.base_url}/extract",
                    files={
                        "file": (
                            request.filename,
                            request.content,
                            request.content_type
                            or self._guess_content_type(request.filename),
                        ),
                    },
                )
                self._raise_for_status(
                    response=response,
                    service_name="Document processor",
                    error_type=DocumentProcessorClientError,
                )
                raw_body = response.text.strip()
        except httpx.RequestError as error:
            raise DocumentProcessorClientError(
                "Document processor service is unavailable."
            ) from error

        yield {
            "event": "progress",
            "stage": "extracting",
            "current": 2,
            "total": 3,
            "message": "Extracting document text...",
        }

        extracted_text = self._parse_extract_response(raw_body)
        yield {
            "event": "completed",
            "document_id": f"doc-{uuid.uuid4().hex}",
            "filename": request.filename,
            "extracted_text": extracted_text,
            "page_count": 0,
        }

    def _guess_content_type(self, filename: str) -> str:
        """Infer the content type for a filename.

        Args:
            filename (str): The filename to inspect.

        Returns:
            str: The guessed MIME type or a generic binary MIME type.
        """
        guessed_type, _ = mimetypes.guess_type(filename)
        return guessed_type or "application/octet-stream"

    def _parse_extract_response(self, raw_body: str) -> str:
        """Parse the document-processor text extraction response.

        Args:
            raw_body (str): The raw HTTP response body.

        Returns:
            str: The extracted text returned by document-processor.
        """
        if not raw_body:
            return ""

        try:
            payload = json.loads(raw_body)
        except json.JSONDecodeError:
            return raw_body

        if isinstance(payload, str):
            return payload

        if isinstance(payload, dict):
            value = payload.get("text") or payload.get("extracted_text")
            if isinstance(value, str):
                return value

        return str(payload)
