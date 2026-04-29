"""HTTP client for consuming the privacy-shield service."""
from __future__ import annotations

import contextlib
import json
from collections.abc import Iterator
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from infrastructure.ports.external.privacy_shield_port import (
    PrivacyShieldMessageStreamRequest, PrivacyShieldPort,
    PrivacyShieldStreamChunk, PrivacyShieldStreamCompleted,
    PrivacyShieldStreamEvent, PrivacyShieldStreamFailed,
    PrivacyShieldStreamRequest)


class PrivacyShieldError(RuntimeError):
    """Represent a failure when communicating with privacy-shield."""


@dataclass(frozen=True)
class HttpPrivacyShieldClient(PrivacyShieldPort):
    """Implement the privacy-shield port over HTTP.

    This adapter sends original user prompts to privacy-shield. Privacy-shield
    owns anonymization, assistant API calls, deanonymization, and the safe
    stream returned to web-ui.

    Attributes:
        base_url (str): The base URL of the privacy-shield service.
    """

    base_url: str = "http://127.0.0.1:7002"

    def stream_message_response(
        self,
        request: PrivacyShieldMessageStreamRequest,
    ) -> Iterator[PrivacyShieldStreamEvent]:
        """Send a user prompt to privacy-shield and stream safe response events.

        Args:
            request (PrivacyShieldMessageStreamRequest): The message stream request
                containing the chat identifier and original user prompt.

        Returns:
            Iterator[PrivacyShieldStreamEvent]: The streamed safe response events.

        Raises:
            PrivacyShieldError: If the service is unavailable, returns an HTTP
                error, or emits an unknown event.
        """
        payload = json.dumps(
            {
                "chat_id": request.chat_id,
                "text": request.content,
            }
        ).encode("utf-8")

        http_request = Request(
            url=f"{self.base_url}/anonymize",
            data=payload,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Content-Length": str(len(payload)),
            },
        )

        try:
            response = urlopen(http_request, timeout=600)
        except HTTPError as error:
            raise PrivacyShieldError(
                f"Privacy-shield request failed with status {error.code}."
            ) from error
        except URLError as error:
            raise PrivacyShieldError(
                "Privacy-shield service is unavailable."
            ) from error

        with contextlib.closing(response) as stream:
            for raw_line in stream:
                line = raw_line.decode("utf-8").strip()
                if not line:
                    continue
                yield self._parse_stream_event(line)

    def stream_safe_response(
        self,
        request: PrivacyShieldStreamRequest,
    ) -> Iterator[PrivacyShieldStreamEvent]:
        """Request a safe response stream for a processed document.

        Args:
            request (PrivacyShieldStreamRequest): The request containing the chat
                and document identifiers.

        Returns:
            Iterator[PrivacyShieldStreamEvent]: The streamed safe response events.

        Raises:
            PrivacyShieldError: If the service is unavailable, returns an HTTP
                error, or emits an unknown event.
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

        try:
            response = urlopen(http_request, timeout=600)
        except HTTPError as error:
            raise PrivacyShieldError(
                f"Privacy-shield request failed with status {error.code}."
            ) from error
        except URLError as error:
            raise PrivacyShieldError(
                "Privacy-shield service is unavailable."
            ) from error

        with contextlib.closing(response) as stream:
            for raw_line in stream:
                line = raw_line.decode("utf-8").strip()
                if not line:
                    continue
                yield self._parse_stream_event(line)

    def _parse_stream_event(self, payload: str) -> PrivacyShieldStreamEvent:
        """Convert one NDJSON line into a typed privacy-shield event.

        Args:
            payload (str): The JSON-encoded event payload.

        Returns:
            PrivacyShieldStreamEvent: The parsed stream event.

        Raises:
            PrivacyShieldError: If the event type is unknown.
        """
        parsed = json.loads(payload)
        event_type = parsed["event"]

        if event_type == "chunk":
            return PrivacyShieldStreamChunk(
                event="chunk",
                content=parsed["content"],
            )

        if event_type == "completed":
            return PrivacyShieldStreamCompleted(event="completed")

        if event_type == "error":
            return PrivacyShieldStreamFailed(
                event="error",
                detail=parsed["detail"],
            )

        raise PrivacyShieldError(
            "Unknown privacy-shield event received."
        )
