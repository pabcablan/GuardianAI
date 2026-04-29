"""HTTP document client that routes uploads through orchestrator."""
from __future__ import annotations

import contextlib
import json
import mimetypes
import uuid
from collections.abc import Iterator
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from infrastructure.ports.external.orchestrator_document_port import (
    OrchestratorDocumentEvent,
    OrchestratorDocumentPort,
    ProcessDocumentCompletedEvent,
    ProcessDocumentErrorEvent,
    ProcessDocumentProgressEvent,
    ProcessDocumentRequest,
)


class OrchestratorDocumentError(RuntimeError):
    """Represent a failure while processing documents through orchestrator."""


@dataclass(frozen=True)
class HttpOrchestratorDocumentClient(OrchestratorDocumentPort):
    """Implement document processing through the orchestrator API.

    Attributes:
        base_url (str): The orchestrator API base URL.
    """

    base_url: str = "http://127.0.0.1:7003"

    def stream_process_document(
        self,
        request: ProcessDocumentRequest,
    ) -> Iterator[OrchestratorDocumentEvent]:
        """Send a PDF to orchestrator and stream document processing events.

        Args:
            request (ProcessDocumentRequest): The document processing request.

        Returns:
            Iterator[OrchestratorDocumentEvent]: The parsed processing events.
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
            raise OrchestratorDocumentError(detail) from error
        except URLError as error:
            raise OrchestratorDocumentError(
                "Orchestrator service is unavailable."
            ) from error

        with contextlib.closing(response) as stream:
            for raw_line in stream:
                line = raw_line.decode("utf-8").strip()
                if not line:
                    continue
                yield self._parse_stream_event(line)

    def _build_multipart_payload(
        self,
        request: ProcessDocumentRequest,
        boundary: str,
    ) -> bytes:
        """Build the multipart/form-data body used to upload the file.

        Args:
            request (ProcessDocumentRequest): The processing request.
            boundary (str): The multipart boundary.

        Returns:
            bytes: The encoded multipart request body.
        """
        content_type = request.content_type or self._guess_content_type(
            request.filename
        )
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
            str: The orchestrator error detail or a fallback message.
        """
        fallback_message = (
            "Orchestrator document request failed with status "
            f"{error.code}."
        )

        try:
            payload = json.loads(error.read().decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return fallback_message

        return payload.get("detail", fallback_message)

    def _parse_stream_event(self, payload: str) -> OrchestratorDocumentEvent:
        """Convert one NDJSON line from orchestrator into a typed event.

        Args:
            payload (str): The JSON event payload.

        Returns:
            OrchestratorDocumentEvent: The parsed processing event.
        """
        parsed = json.loads(payload)
        event_type = parsed["event"]

        if event_type == "progress":
            return ProcessDocumentProgressEvent(
                event=event_type,
                stage=parsed["stage"],
                current=parsed["current"],
                total=parsed["total"],
                message=parsed["message"],
            )

        if event_type == "completed":
            return ProcessDocumentCompletedEvent(
                event=event_type,
                document_id=parsed["document_id"],
                filename=parsed["filename"],
                extracted_text=parsed.get("extracted_text", ""),
                page_count=parsed.get("page_count", 0),
            )

        if event_type == "error":
            return ProcessDocumentErrorEvent(
                event=event_type,
                detail=parsed["detail"],
            )

        raise OrchestratorDocumentError("Unknown orchestrator event received.")
