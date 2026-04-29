"""Fake assistant stream gateway used while the ChatGPT API is pending."""
from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass


@dataclass(frozen=True)
class FakeAssistantStreamGateway:
    """Return streamed fake assistant chunks for an anonymized prompt.

    Attributes:
        chunk_size (int): The maximum size used to split generated chunks.
    """

    chunk_size: int = 18

    def stream_response(self, prompt: str) -> Iterator[str]:
        """Stream a fake assistant response for an anonymized prompt.

        Args:
            prompt (str): The anonymized prompt sent to the assistant.

        Returns:
            Iterator[str]: The fake assistant response chunks.
        """
        response = (
            "Respuesta fake generada para el prompt anonimizado: "
            f"{prompt}"
        )
        for index in range(0, len(response), self.chunk_size):
            yield response[index:index + self.chunk_size]
