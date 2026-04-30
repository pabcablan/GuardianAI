"""HTTP client prepared for consuming the future ai-gateway service."""
from __future__ import annotations

import contextlib
import json
from collections.abc import Iterator
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from infrastructure.ports.ai_gateway_port import (
    AiGatewayPort,
    AssistantStreamRequest,
)


class AiGatewayClientError(RuntimeError):
    """Represent an ai-gateway communication failure."""


@dataclass(frozen=True)
class HttpAiGatewayClient(AiGatewayPort):
    """Call the future ai-gateway HTTP stream endpoint.

    This adapter is intentionally not wired into the running container yet. The
    application still uses the fake gateway until the ai-gateway module is
    available.

    Attributes:
        base_url (str): The ai-gateway API base URL.
    """

    base_url: str = "http://127.0.0.1:7004"

    def stream_response(
        self,
        request: AssistantStreamRequest,
    ) -> Iterator[str]:
        """Stream an anonymized assistant response from ai-gateway.

        Args:
            request (AssistantStreamRequest): The assistant stream request.

        Returns:
            Iterator[str]: The anonymized assistant response chunks.
        """
        payload = json.dumps(
            {
                "chat_id": request.chat_id,
                "prompt": request.prompt,
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

        try:
            response = urlopen(http_request, timeout=600)
        except HTTPError as error:
            detail = self._read_error_detail(error)
            raise AiGatewayClientError(
                f"Ai-gateway request failed with status {error.code}: {detail}"
            ) from error
        except URLError as error:
            raise AiGatewayClientError(
                "Ai-gateway service is unavailable."
            ) from error

        with contextlib.closing(response) as stream:
            for raw_line in stream:
                line = raw_line.decode("utf-8").strip()
                if not line:
                    continue

                yield self._parse_stream_line(line)

    def _parse_stream_line(self, line: str) -> str:
        """Parse one ai-gateway stream line.

        Args:
            line (str): The raw NDJSON line.

        Returns:
            str: The assistant chunk content.
        """
        payload = json.loads(line)
        event_type = payload.get("event")

        if event_type == "chunk":
            return str(payload.get("content", ""))

        if event_type == "completed":
            return ""

        if event_type == "error":
            raise AiGatewayClientError(str(payload.get("detail", "")))

        raise AiGatewayClientError("Unknown ai-gateway event received.")

    def _read_error_detail(self, error: HTTPError) -> str:
        """Read a useful detail from an HTTP error response.

        Args:
            error (HTTPError): The raised HTTP error.

        Returns:
            str: The response body or a fallback message.
        """
        try:
            body = error.read().decode("utf-8").strip()
        except OSError:
            return "No error detail returned."

        return body or "No error detail returned."
