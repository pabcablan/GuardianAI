"""HTTP client for consuming the document processor service."""
from __future__ import annotations

import contextlib
import json
import mimetypes
import uuid
from collections.abc import Iterator
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from infrastructure.ports.external.document_processing_port import (
    DocumentExtractionEvent,
    DocumentProcessingPort,
    ExtractDocumentCompletedEvent,
    ExtractDocumentErrorEvent,
    ExtractDocumentProgressEvent,
    ExtractDocumentRequest,
)


class DocumentProcessingError(RuntimeError):
    """Represent a document processor failure."""


@dataclass(frozen=True)
class HttpDocumentProcessingClient(DocumentProcessingPort):
    """Implement the document processing port over HTTP.

    Attributes:
        base_url (str): The base URL of the document processor service.
    """

    base_url: str = "http://127.0.0.1:8001"

    def stream_extract_document(
        self,
        request: ExtractDocumentRequest,
    ) -> Iterator[DocumentExtractionEvent]:
        """Send a PDF to the processor and stream NDJSON events.

        Args:
            request (ExtractDocumentRequest): The document extraction request.

        Returns:
            Iterator[DocumentExtractionEvent]: The parsed extraction events.

        Raises:
            DocumentProcessingError: If the processor cannot be reached, returns
            an HTTP error, or emits an unknown event.
        """
        boundary = f"boundary-{uuid.uuid4().hex}"
        payload = self._build_multipart_payload(request, boundary)
        http_request = Request(
            url=f"{self.base_url}/api/documents/extract-stream",
            data=payload,
            method="POST",
            headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "Content-Length": str(len(payload)),
            },
        )

        try:
            response = urlopen(http_request, timeout=600)
        except HTTPError as error:
            detail = self._read_error_detail(error)
            raise DocumentProcessingError(detail) from error
        except URLError as error:
            raise DocumentProcessingError(
                "Document processor service is unavailable."
            ) from error

        with contextlib.closing(response) as stream:
            for raw_line in stream:
                line = raw_line.decode("utf-8").strip()
                if not line:
                    continue
                yield self._parse_stream_event(line)

    def _build_multipart_payload(
        self,
        request: ExtractDocumentRequest,
        boundary: str,
    ) -> bytes:
        """Build the multipart/form-data body used to upload the file.

        Args:
            request (ExtractDocumentRequest): The extraction request.
            boundary (str): The multipart boundary.

        Returns:
            bytes: The encoded multipart request body.
        """
        content_type = request.content_type or self._guess_content_type(request.filename)
        lines = [
            f"--{boundary}".encode("utf-8"),
            (
                "Content-Disposition: form-data; "
                f'name="file"; filename="{request.filename}"'
            ).encode("utf-8"),
            f"Content-Type: {content_type}".encode("utf-8"),
            b"",
            request.content,
            f"--{boundary}--".encode("utf-8"),
            b"",
        ]
        return b"\r\n".join(lines)

    def _guess_content_type(self, filename: str) -> str:
        """Infer the content type for a filename.

        Args:
            filename (str): The filename to inspect.

        Returns:
            str: The guessed MIME type, or a generic binary MIME type.
        """
        guessed_type, _ = mimetypes.guess_type(filename)
        return guessed_type or "application/octet-stream"

    def _read_error_detail(self, error: HTTPError) -> str:
        """Extract a readable error message from an HTTP response.

        Args:
            error (HTTPError): The HTTP error raised by urlopen.

        Returns:
            str: The processor error detail or a fallback message.
        """
        fallback_message = f"Document processor request failed with status {error.code}."

        try:
            payload = json.loads(error.read().decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return fallback_message

        return payload.get("detail", fallback_message)

    def _parse_stream_event(self, payload: str) -> DocumentExtractionEvent:
        """Convert one NDJSON line from the processor into a typed event.

        Args:
            payload (str): The JSON event payload.

        Returns:
            DocumentExtractionEvent: The parsed extraction event.

        Raises:
            DocumentProcessingError: If the event type is unknown.
        """
        parsed = json.loads(payload)
        event_type = parsed["event"]

        if event_type == "progress":
            return ExtractDocumentProgressEvent(
                event=event_type,
                stage=parsed["stage"],
                current=parsed["current"],
                total=parsed["total"],
                message=parsed["message"],
            )

        if event_type == "completed":
            return ExtractDocumentCompletedEvent(
                event=event_type,
                document_id=parsed["document_id"],
                filename=parsed["filename"],
                extracted_text=parsed["extracted_text"],
                page_count=parsed["page_count"],
            )

        if event_type == "error":
            return ExtractDocumentErrorEvent(
                event=event_type,
                detail=parsed["detail"],
            )

        raise DocumentProcessingError("Unknown document processor event received.")
