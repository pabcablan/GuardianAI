"""HTTP client for consuming orchestrator response streams."""
from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass

import httpx

from infrastructure.adapters.orchestrator.base import (
    OrchestratorClientError,
    OrchestratorHttpClientBase,
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


@dataclass(frozen=True)
class HttpOrchestratorResponseClient(
    OrchestratorHttpClientBase,
    OrchestratorResponsePort,
):
    """Consume prompt and document response streams from orchestrator."""

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
        yield from self._consume_stream(
            path="/api/messages/stream",
            json_payload={
                "chat_id": request.chat_id,
                "text": request.content,
            },
        )

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
        yield from self._consume_stream(
            path="/api/documents/safe-stream",
            json_payload={
                "chat_id": request.chat_id,
                "document_id": request.document_id,
            },
        )

    def _consume_stream(
        self,
        path: str,
        json_payload: dict[str, str],
    ) -> Iterator[OrchestratorStreamEvent]:
        """Consume an NDJSON response stream.

        Args:
            path (str): The orchestrator API path.
            json_payload (dict[str, str]): The JSON request body.

        Returns:
            Iterator[OrchestratorStreamEvent]: Parsed stream events.
        """
        try:
            with httpx.stream(
                "POST",
                f"{self.base_url}{path}",
                json=json_payload,
                timeout=self.timeout_seconds,
            ) as response:
                self._raise_for_status(response)
                for line in response.iter_lines():
                    if not line:
                        continue
                    yield self._parse_stream_event(line)
        except httpx.RequestError as error:
            raise OrchestratorClientError(
                "Orchestrator service is unavailable."
            ) from error

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

        raise OrchestratorClientError("Unknown orchestrator event received.")
