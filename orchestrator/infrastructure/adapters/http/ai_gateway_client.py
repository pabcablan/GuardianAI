"""HTTP client prepared for consuming the future ai-gateway service."""
from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass

import httpx

from infrastructure.adapters.http.base import (
    ExternalHttpClientBase,
    ExternalServiceClientError,
)
from infrastructure.ports.ai_gateway_port import (
    AiGatewayPort,
    AssistantStreamRequest,
)


class AiGatewayClientError(ExternalServiceClientError):
    """Represent an ai-gateway communication failure."""


@dataclass(frozen=True)
class HttpAiGatewayClient(ExternalHttpClientBase, AiGatewayPort):
    """Call the future ai-gateway HTTP stream endpoint.

    This adapter is intentionally not wired into the running container yet. The
    application still uses the fake gateway until the ai-gateway module is
    available.
    """

    base_url: str = "http://127.0.0.1:8005"

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
        payload = {
            "chat_id": request.chat_id,
            "prompt": request.prompt,
        }
        try:
            with httpx.stream(
                "POST",
                f"{self.base_url}/api/messages/stream",
                json=payload,
                timeout=self.timeout_seconds,
            ) as response:
                self._raise_for_status(
                    response=response,
                    service_name="Ai-gateway",
                    error_type=AiGatewayClientError,
                    read_stream=True,
                )
                for line in response.iter_lines():
                    if not line:
                        continue

                    yield self._parse_stream_line(line)
        except httpx.RequestError as error:
            raise AiGatewayClientError(
                "Ai-gateway service is unavailable."
            ) from error

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
