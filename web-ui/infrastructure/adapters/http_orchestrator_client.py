"""HTTP client for consuming the orchestrator service."""
from __future__ import annotations

import contextlib
import json
from collections.abc import Iterator
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

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
class HttpOrchestratorClient(OrchestratorResponsePort):
    """Implement the safe stream port through the orchestrator API.

    Attributes:
        base_url (str): The base URL of the orchestrator service.
    """

    base_url: str = "http://127.0.0.1:7003"

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
