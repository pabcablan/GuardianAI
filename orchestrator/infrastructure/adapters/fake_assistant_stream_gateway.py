"""Fake assistant stream gateway used while the ChatGPT API is pending."""
from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from infrastructure.ports.ai_gateway_port import (
    AiGatewayPort,
    AssistantStreamRequest,
)


@dataclass(frozen=True)
class FakeAssistantStreamGateway(AiGatewayPort):
    """Return streamed fake assistant chunks for an anonymized prompt.

    Attributes:
        chunk_size (int): The maximum size used to split generated chunks.
    """

    chunk_size: int = 18

    def stream_response(
        self,
        request: AssistantStreamRequest,
    ) -> Iterator[str]:
        """Stream a fake assistant response for an anonymized prompt.

        Args:
            request (AssistantStreamRequest): The assistant stream request.

        Returns:
            Iterator[str]: The fake assistant response chunks.
        """
        response = (
            "Respuesta fake generada para el prompt anonimizado: "
            f"{request.prompt}"
        )
        for index in range(0, len(response), self.chunk_size):
            yield response[index:index + self.chunk_size]
