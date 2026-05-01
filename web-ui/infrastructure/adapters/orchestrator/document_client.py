"""HTTP client for sending documents to orchestrator."""
from __future__ import annotations

import json
import mimetypes
from collections.abc import Iterator
from dataclasses import dataclass

from infrastructure.adapters.orchestrator.base import (
    OrchestratorClientError,
    OrchestratorHttpClientBase,
)
from infrastructure.ports.external.orchestrator_document_port import (
    OrchestratorDocumentEvent,
    OrchestratorDocumentPort,
    ProcessDocumentCompletedEvent,
    ProcessDocumentErrorEvent,
    ProcessDocumentProgressEvent,
    ProcessDocumentRequest,
)


@dataclass(frozen=True)
class HttpOrchestratorDocumentClient(
    OrchestratorHttpClientBase,
    OrchestratorDocumentPort,
):
    """Send document uploads to orchestrator."""

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
        yield from self._consume_document_stream(
            data={"prompt": request.prompt},
            files={
                "file": (
                    request.filename,
                    request.content,
                    request.content_type
                    or self._guess_content_type(request.filename),
                ),
            },
        )

    def _consume_document_stream(
        self,
        data: dict[str, str],
        files: dict[str, tuple[str, bytes, str]],
    ) -> Iterator[OrchestratorDocumentEvent]:
        """Consume an NDJSON document processing response stream.

        Args:
            data (dict[str, str]): Form fields sent with the file.
            files (dict[str, tuple[str, bytes, str]]): Uploaded files.

        Returns:
            Iterator[OrchestratorDocumentEvent]: Parsed document events.
        """
        for line in self._stream_form_lines(
            path="/api/documents/extract-stream",
            data=data,
            files=files,
        ):
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

        raise OrchestratorClientError(
            "Unknown orchestrator document event received."
        )

    def _guess_content_type(self, filename: str) -> str:
        """Infer the content type for a filename.

        Args:
            filename (str): The filename to inspect.

        Returns:
            str: The guessed MIME type, or a generic binary MIME type.
        """
        guessed_type, _ = mimetypes.guess_type(filename)
        return guessed_type or "application/octet-stream"
