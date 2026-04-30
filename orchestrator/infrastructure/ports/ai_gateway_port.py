"""Port for requesting assistant streams from ai-gateway."""
from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class AssistantStreamRequest:
    """Represent a request sent to the assistant gateway.

    Attributes:
        chat_id (str): The chat that owns the request.
        prompt (str): The anonymized prompt sent to the assistant.
    """

    chat_id: str
    prompt: str


class AiGatewayPort(Protocol):
    """Define how orchestrator consumes assistant response streams."""

    def stream_response(
        self,
        request: AssistantStreamRequest,
    ) -> Iterator[str]:
        """Stream an assistant response for an anonymized prompt.

        Args:
            request (AssistantStreamRequest): The assistant stream request.

        Returns:
            Iterator[str]: The anonymized assistant response chunks.
        """
