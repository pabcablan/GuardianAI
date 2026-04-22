from __future__ import annotations

import json
import mimetypes
import uuid
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from infrastructure.ports.external.document_processing_port import (
    DocumentProcessingPort,
    ExtractDocumentRequest,
    ExtractDocumentResponse,
)


class DocumentProcessingError(RuntimeError):
    """Raised when the document-processor module cannot process a document."""


@dataclass(frozen=True)
class HttpDocumentProcessingClient(DocumentProcessingPort):
    base_url: str = "http://127.0.0.1:8001"

    def extract_document(
        self,
        request: ExtractDocumentRequest,
    ) -> ExtractDocumentResponse:
        boundary = f"boundary-{uuid.uuid4().hex}"
        payload = self._build_multipart_payload(request, boundary)
        http_request = Request(
            url=f"{self.base_url}/api/documents/extract",
            data=payload,
            method="POST",
            headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "Content-Length": str(len(payload)),
            },
        )

        try:
            with urlopen(http_request, timeout=120) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            detail = self._read_error_detail(error)
            raise DocumentProcessingError(detail) from error
        except URLError as error:
            raise DocumentProcessingError(
                "Document processor service is unavailable."
            ) from error

        return ExtractDocumentResponse(
            document_id=response_payload["document_id"],
            filename=response_payload["filename"],
            extracted_text=response_payload["extracted_text"],
            page_count=response_payload["page_count"],
        )

    def _build_multipart_payload(
        self,
        request: ExtractDocumentRequest,
        boundary: str,
    ) -> bytes:
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
        guessed_type, _ = mimetypes.guess_type(filename)
        return guessed_type or "application/octet-stream"

    def _read_error_detail(self, error: HTTPError) -> str:
        fallback_message = f"Document processor request failed with status {error.code}."

        try:
            payload = json.loads(error.read().decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return fallback_message

        return payload.get("detail", fallback_message)
