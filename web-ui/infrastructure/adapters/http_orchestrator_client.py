"""HTTP client for consuming the orchestrator service."""
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
from infrastructure.ports.external.orchestrator_response_port import (
    OrchestratorDocumentResponseRequest,
    OrchestratorMessageResponseRequest,
    OrchestratorResponsePort,
    OrchestratorStreamChunk,
    OrchestratorStreamCompleted,
    OrchestratorStreamEvent,
    OrchestratorStreamFailed,
)


class OrchestratorError(RuntimeError):
    """Represent a failure when communicating with orchestrator."""


@dataclass(frozen=True)
class HttpOrchestratorClient(
    OrchestratorResponsePort,
    OrchestratorDocumentPort,
):
    """Implement web-ui orchestration ports through the orchestrator API.

    Attributes:
        base_url (str): The base URL of the orchestrator service.
    """

    base_url: str = "http://127.0.0.1:8003"

    def stream_message_response(
        self,
        request: OrchestratorMessageResponseRequest,
    ) -> Iterator[OrchestratorStreamEvent]:
        """Send a user prompt to orchestrator and stream safe response events.

        Args:
            request (OrchestratorMessageResponseRequest): The chat identifier
                and original user prompt.

        Returns:
            Iterator[OrchestratorStreamEvent]: The safe stream events.
        """
        payload = json.dumps(
            {
                "chat_id": request.chat_id,
                "text": request.content,
            }
        ).encode("utf-8")

        http_request = Request(
            url=f"{self.base_url}/api/messages/stream",
            data=payload,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Content-Length": str(len(payload)),
            },
        )
        yield from self._consume_stream(http_request)

    def stream_safe_response(
        self,
        request: OrchestratorDocumentResponseRequest,
    ) -> Iterator[OrchestratorStreamEvent]:
        """Stream a document response through orchestrator.

        Args:
            request (OrchestratorDocumentResponseRequest): The document stream
                request.

        Returns:
            Iterator[OrchestratorStreamEvent]: The safe stream events.
        """
        payload = json.dumps(
            {
                "chat_id": request.chat_id,
                "document_id": request.document_id,
            }
        ).encode("utf-8")

        http_request = Request(
            url=f"{self.base_url}/api/documents/safe-stream",
            data=payload,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Content-Length": str(len(payload)),
            },
        )
        yield from self._consume_stream(http_request)

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
        yield from self._consume_document_stream(http_request)

    def _consume_stream(
        self,
        request: Request,
    ) -> Iterator[OrchestratorStreamEvent]:
        """Consume an NDJSON response stream.

        Args:
            request (Request): The configured HTTP request.

        Returns:
            Iterator[OrchestratorStreamEvent]: Parsed stream events.
        """
        try:
            response = urlopen(request, timeout=600)
        except HTTPError as error:
            raise OrchestratorError(
                f"Orchestrator request failed with status {error.code}."
            ) from error
        except URLError as error:
            raise OrchestratorError(
                "Orchestrator service is unavailable."
            ) from error

        with contextlib.closing(response) as stream:
            for raw_line in stream:
                line = raw_line.decode("utf-8").strip()
                if not line:
                    continue
                yield self._parse_stream_event(line)

    def _parse_stream_event(self, payload: str) -> OrchestratorStreamEvent:
        """Convert one NDJSON line into a typed stream event.

        Args:
            payload (str): The JSON-encoded event payload.

        Returns:
            OrchestratorStreamEvent: The parsed stream event.
        """
        parsed = json.loads(payload)
        event_type = parsed["event"]

        if event_type == "chunk":
            return OrchestratorStreamChunk(
                event="chunk",
                content=parsed["content"],
            )

        if event_type == "completed":
            return OrchestratorStreamCompleted(event="completed")

        if event_type == "error":
            return OrchestratorStreamFailed(
                event="error",
                detail=parsed["detail"],
            )

        raise OrchestratorError("Unknown orchestrator event received.")

    def _consume_document_stream(
        self,
        request: Request,
    ) -> Iterator[OrchestratorDocumentEvent]:
        """Consume an NDJSON document processing response stream.

        Args:
            request (Request): The configured HTTP request.

        Returns:
            Iterator[OrchestratorDocumentEvent]: Parsed document events.
        """
        try:
            response = urlopen(request, timeout=600)
        except HTTPError as error:
            raise OrchestratorError(
                f"Orchestrator request failed with status {error.code}."
            ) from error
        except URLError as error:
            raise OrchestratorError(
                "Orchestrator service is unavailable."
            ) from error

        with contextlib.closing(response) as stream:
            for raw_line in stream:
                line = raw_line.decode("utf-8").strip()
                if not line:
                    continue
                yield self._parse_document_event(line)

    def _parse_document_event(
        self,
        payload: str,
    ) -> OrchestratorDocumentEvent:
        """Convert one NDJSON line into a typed document event.

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

        raise OrchestratorError("Unknown orchestrator document event received.")

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
            b'Content-Disposition: form-data; name="prompt"',
            b"",
            request.prompt.encode("utf-8"),
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
