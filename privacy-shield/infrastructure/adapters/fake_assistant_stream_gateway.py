"""Fake assistant stream gateway used to test streaming deanonymization."""
from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field

from infrastructure.ports.external.assistant_stream_port import (
    AssistantStreamPort,
)


@dataclass
class FakeAssistantStreamGateway(AssistantStreamPort):
    """Return fake assistant chunks for tests and demos.

    Attributes:
        responses (dict[str, tuple[str, ...]]): Mapping between prompts and
            fake response chunks.
        chunk_size (int): The maximum size used to split generated fake chunks.
    """

    responses: dict[str, tuple[str, ...]] = field(default_factory=dict)
    chunk_size: int = 18

    def stream_response(self, prompt: str) -> Iterator[str]:
        """Stream the fake response configured for a prompt.

        Args:
            prompt (str): The anonymized prompt.

        Returns:
            Iterator[str]: The configured fake chunks or chunks containing the
            anonymized prompt.
        """
        if prompt in self.responses:
            yield from self.responses[prompt]
            return

        yield from self._split_into_chunks(
            f"Respuesta fake generada para el prompt anonimizado: {prompt}"
        )

    def _split_into_chunks(self, text: str) -> Iterator[str]:
        """Split text into small chunks to simulate a streamed response.

        Args:
            text (str): The text to split.

        Returns:
            Iterator[str]: The generated text chunks.
        """
        for index in range(0, len(text), self.chunk_size):
            yield text[index:index + self.chunk_size]
