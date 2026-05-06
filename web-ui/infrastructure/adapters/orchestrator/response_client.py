"""HTTP client for consuming orchestrator response streams."""
from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass

from infrastructure.adapters.orchestrator.base import (
    OrchestratorClientError,
    OrchestratorHttpClientBase,
)
from infrastructure.ports.external.orchestrator_response_port import (
    OrchestratorAnonymizationPreview,
    OrchestratorAnonymizationPreviewRequest,
    OrchestratorAnonymizedPrompt,
    OrchestratorAnonymizedResponseRequest,
    OrchestratorDocumentAnonymizationPreviewRequest,
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

    def preview_message_anonymization(
        self,
        request: OrchestratorAnonymizationPreviewRequest,
    ) -> OrchestratorAnonymizationPreview:
        """Return anonymized prompt text without calling the assistant."""
        payload = self._post_json(
            path="/api/messages/anonymize-preview",
            payload={
                "chat_id": request.chat_id,
                "text": request.content,
                "model": request.model,
            },
        )
        return self._parse_preview_payload(payload)

    def preview_document_anonymization(
        self,
        request: OrchestratorDocumentAnonymizationPreviewRequest,
    ) -> OrchestratorAnonymizationPreview:
        """Return anonymized document text without calling the assistant."""
        payload = self._post_json(
            path="/api/documents/anonymize-preview",
            payload={
                "chat_id": request.chat_id,
                "document_id": request.document_id,
            },
        )
        return self._parse_preview_payload(payload)

    def stream_anonymized_response(
        self,
        request: OrchestratorAnonymizedResponseRequest,
    ) -> Iterator[OrchestratorStreamEvent]:
        """Stream a response from already anonymized text."""
        yield from self._consume_stream(
            path="/api/anonymized/stream",
            json_payload={
                "chat_id": request.chat_id,
                "anonymized_text": request.anonymized_content,
                "anonymization_id": request.anonymization_id,
                "model": request.model,
            },
        )

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
                "model": request.model,
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
                "model": request.model,
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
        for line in self._stream_json_lines(path=path, payload=json_payload):
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

        if event_type == "anonymized_prompt":
            return OrchestratorAnonymizedPrompt(
                event="anonymized_prompt",
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

    def _parse_preview_payload(
        self,
        payload: dict[str, object],
    ) -> OrchestratorAnonymizationPreview:
        """Convert an orchestrator preview payload into a typed object.

        Args:
            payload (dict[str, object]): The preview response payload.

        Returns:
            OrchestratorAnonymizationPreview: The typed preview result.
        """
        return OrchestratorAnonymizationPreview(
            anonymized_content=str(payload["anonymized_text"]),
            anonymization_id=str(payload["anonymization_id"]),
            replacement_count=int(payload.get("replacement_count", 0)),
        )
