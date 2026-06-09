"""HTTP client for consuming the ai-gateway service."""
from __future__ import annotations

import json
import os
from collections.abc import AsyncIterator
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
    org_id: str = os.getenv("AI_GATEWAY_ORG_ID", "guardianai")

    async def stream_response(
        self,
        request: AssistantStreamRequest,
    ) -> AsyncIterator[str]:
        """Stream an anonymized assistant response from ai-gateway.

        Args:
            request (AssistantStreamRequest): The assistant stream request.

        Returns:
            AsyncIterator[str]: The anonymized assistant response chunks.
        """
        try:
            async with httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout_seconds,
            ) as client:
                async for chunk in self._stream_completion(
                    client=client,
                    messages=[
                        {
                            "role": message.role,
                            "content": message.content,
                        }
                        for message in request.messages
                    ],
                    model=request.model,
                ):
                    yield chunk
        except httpx.RequestError as error:
            raise AiGatewayClientError(
                "Ai-gateway service is unavailable."
            ) from error

    async def _stream_completion(
        self,
        client: httpx.AsyncClient,
        messages: list[dict[str, str]],
        model: str,
    ) -> AsyncIterator[str]:
        """Stream a completion from ai-gateway.

        Args:
            client (httpx.AsyncClient): The configured HTTP client.
            messages (list[dict[str, str]]): The anonymized messages sent to
                the model.
            model (str): The AI model selected by the user.

        Yields:
            str: Assistant response chunks.
        """
        payload = {
            "messages": messages,
            "model": model,
        }

        async with client.stream(
            "POST",
            "/handle",
            json=payload,
            timeout=self.timeout_seconds,
        ) as response:
            if not response.is_success:
                await response.aread()
            self._raise_for_status(
                response=response,
                service_name="Ai-gateway",
                error_type=AiGatewayClientError,
            )
            async for line in response.aiter_lines():
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

        if payload.startswith("{"):
            parsed = json.loads(payload)
            if parsed.get("type") == "chunk":
                return str(parsed.get("content", ""))

        return payload
