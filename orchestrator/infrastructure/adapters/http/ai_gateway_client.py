"""HTTP client for consuming the ai-gateway service."""
from __future__ import annotations

import os
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
    """Call ai-gateway session and completion endpoints."""

    base_url: str = os.getenv(
        "AI_GATEWAY_BASE_URL",
        "http://127.0.0.1:8005",
    )
    model: str = os.getenv("AI_GATEWAY_MODEL", "gpt-4.1-mini")
    org_id: str = os.getenv("AI_GATEWAY_ORG_ID", "guardianai")

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
        try:
            with httpx.Client(
                base_url=self.base_url,
                timeout=self.timeout_seconds,
            ) as client:
                yield from self._stream_completion(
                    client=client,
                    prompt=request.prompt,
                )
        except httpx.RequestError as error:
            raise AiGatewayClientError(
                "Ai-gateway service is unavailable."
            ) from error

    def _stream_completion(
        self,
        client: httpx.Client,
        prompt: str,
    ) -> Iterator[str]:
        """Stream a completion from ai-gateway.

        Args:
            client (httpx.Client): The configured HTTP client.
            prompt (str): The anonymized prompt sent to the model.

        Yields:
            str: Assistant response chunks.
        """
        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "model": self.model,
        }

        with client.stream(
            "POST",
            "/handle",
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

                chunk = self._parse_sse_line(line)
                if chunk:
                    yield chunk

    def _parse_sse_line(self, line: str) -> str:
        """Parse one ai-gateway SSE line.

        Args:
            line (str): The raw SSE line.

        Returns:
            str: The assistant chunk content.
        """
        if not line.startswith("data:"):
            return ""

        payload = line.removeprefix("data:")
        if payload.startswith(" "):
            payload = payload[1:]

        if payload == "" or payload == "[DONE]":
            return ""

        if payload.startswith("error:"):
            raise AiGatewayClientError(
                f"Ai-gateway stream failed with {payload}."
            )

        return payload
