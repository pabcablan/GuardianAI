"""HTTP client used by the orchestrator to call document-processor."""
from __future__ import annotations

import contextlib
import json
import mimetypes
import uuid
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class DocumentProcessorClientError(RuntimeError):
    """Represent a document-processor communication failure."""


@dataclass(frozen=True)
class DocumentUpload:
    """Represent a document upload sent to document-processor.

    Attributes:
        filename (str): The uploaded filename.
        content_type (str): The uploaded content type.
        content (bytes): The uploaded file content.
    """

    filename: str
    content_type: str
    content: bytes


@dataclass(frozen=True)
class HttpDocumentProcessingClient:
    """Call document-processor HTTP endpoints from orchestrator.

    Attributes:
        base_url (str): The document-processor API base URL.
    """

    base_url: str = "http://127.0.0.1:8001"

    def stream_extract_document(
        self,
        upload: DocumentUpload,
    ) -> Iterator[dict[str, Any]]:
        """Send a PDF to document-processor and stream extraction events.

        Args:
            upload (DocumentUpload): The document upload data.

        Returns:
            Iterator[dict[str, Any]]: Parsed NDJSON events from the processor.
        """
        boundary = f"boundary-{uuid.uuid4().hex}"
        payload = self._build_multipart_payload(upload, boundary)
        request = Request(
            url=f"{self.base_url}/api/documents/extract-stream",
            data=payload,
            method="POST",
            headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "Content-Length": str(len(payload)),
            },
        )

        try:
            response = urlopen(request, timeout=600)
        except HTTPError as error:
            detail = self._read_error_detail(error)
            raise DocumentProcessorClientError(detail) from error
        except URLError as error:
            raise DocumentProcessorClientError(
                "Document processor service is unavailable."
            ) from error

        with contextlib.closing(response) as stream:
            for raw_line in stream:
                line = raw_line.decode("utf-8").strip()
                if not line:
                    continue
                yield json.loads(line)

    def _build_multipart_payload(
        self,
        upload: DocumentUpload,
        boundary: str,
    ) -> bytes:
        """Build the multipart/form-data body used to upload a file.

        Args:
            upload (DocumentUpload): The upload data.
            boundary (str): The multipart boundary.

        Returns:
            bytes: The encoded multipart request body.
        """
        content_type = upload.content_type or self._guess_content_type(
            upload.filename
        )
        lines = [
            f"--{boundary}".encode("utf-8"),
            (
                "Content-Disposition: form-data; "
                f'name="file"; filename="{upload.filename}"'
            ).encode("utf-8"),
            f"Content-Type: {content_type}".encode("utf-8"),
            b"",
            upload.content,
            f"--{boundary}--".encode("utf-8"),
            b"",
        ]
        return b"\r\n".join(lines)

    def _guess_content_type(self, filename: str) -> str:
        """Infer the content type for a filename.

        Args:
            filename (str): The filename to inspect.

        Returns:
            str: The guessed MIME type or a generic binary MIME type.
        """
        guessed_type, _ = mimetypes.guess_type(filename)
        return guessed_type or "application/octet-stream"

    def _read_error_detail(self, error: HTTPError) -> str:
        """Read a useful detail from an HTTP error response.

        Args:
            error (HTTPError): The raised HTTP error.

        Returns:
            str: The response body or a fallback message.
        """
        fallback = (
            "Document processor request failed with status "
            f"{error.code}."
        )

        try:
            payload = json.loads(error.read().decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return fallback

        return payload.get("detail", fallback)
