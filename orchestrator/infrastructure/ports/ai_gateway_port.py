"""Port for requesting assistant streams from ai-gateway."""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass


@dataclass(frozen=True)
class AssistantMessage:
    """Represent one message sent to the assistant gateway.

    Attributes:
        role (str): The message role accepted by ai-gateway.
        content (str): The anonymized message content.
    """

    role: str
    content: str


@dataclass(frozen=True)
class AssistantStreamRequest:
    """Represent a request sent to the assistant gateway.

    Attributes:
        chat_id (str): The chat that owns the request.
        messages (list[AssistantMessage]): The anonymized chat history plus
            the current anonymized prompt.
        model (str): The AI model selected by the user.
    """

    chat_id: str
    messages: list[AssistantMessage]
    model: str


class AiGatewayPort(ABC):
    """Define how orchestrator consumes assistant response streams."""

    @abstractmethod
    async def stream_response(
        self,
        request: AssistantStreamRequest,
    ) -> AsyncIterator[str]:
        """Stream an assistant response for an anonymized prompt.

        Args:
            request (AssistantStreamRequest): The assistant stream request.

        Returns:
            AsyncIterator[str]: The anonymized assistant response chunks.
        """
        ...
