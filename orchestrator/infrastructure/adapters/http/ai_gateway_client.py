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
                session_id = self._create_session(
                    client=client,
                    chat_id=request.chat_id,
                )
                yield from self._stream_completion(
                    client=client,
                    session_id=session_id,
                    prompt=request.prompt,
                )
        except httpx.RequestError as error:
            raise AiGatewayClientError(
                "Ai-gateway service is unavailable."
            ) from error

    def _create_session(self, client: httpx.Client, chat_id: str) -> str:
        """Create an ai-gateway session for a chat.

        Args:
            client (httpx.Client): The configured HTTP client.
            chat_id (str): The chat identifier used as user identifier.

        Returns:
            str: The created ai-gateway session identifier.
        """
        response = client.post(
            "/session",
            json={
                "user_id": chat_id,
                "org_id": self.org_id,
            },
        )
        self._raise_for_status(
            response=response,
            service_name="Ai-gateway",
            error_type=AiGatewayClientError,
        )

        payload = response.json()
        session_id = str(payload.get("session_id", "")).strip()
        if not session_id:
            raise AiGatewayClientError(
                "Ai-gateway did not return a session_id."
            )

        return session_id

    def _stream_completion(
        self,
        client: httpx.Client,
        session_id: str,
        prompt: str,
    ) -> Iterator[str]:
        """Stream a completion from ai-gateway.

        Args:
            client (httpx.Client): The configured HTTP client.
            session_id (str): The ai-gateway session identifier.
            prompt (str): The anonymized prompt sent to the model.

        Yields:
            str: Assistant response chunks.
        """
        payload = {
            "session_id": session_id,
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
            "/complete",
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
