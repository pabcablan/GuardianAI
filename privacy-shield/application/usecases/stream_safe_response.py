"""Use case for streaming and restoring anonymized assistant responses."""
from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Mapping

from domain.streaming_deanonymization import StreamingDeanonymizer
from infrastructure.ports.external.assistant_stream_port import (
    AssistantStreamPort,
)


@dataclass(frozen=True)
class StreamSafeResponseCommand:
    """Represent the input required to stream a restored assistant response.

    Attributes:
        anonymized_prompt (str): The prompt with anonymized placeholders.
        replacements (Mapping[str, str]): The placeholder-to-original-value map.
        strict (bool): Whether unknown placeholders should fail restoration.
    """

    anonymized_prompt: str
    replacements: Mapping[str, str]
    strict: bool = True


class StreamSafeResponseUseCase:
    """Stream an assistant response after restoring anonymized placeholders."""

    def __init__(self, assistant_gateway: AssistantStreamPort) -> None:
        """Initialize the use case.

        Args:
            assistant_gateway (AssistantStreamPort): The streamed assistant
                response provider.
        """
        self._assistant_gateway = assistant_gateway

    def execute(self, command: StreamSafeResponseCommand) -> Iterator[str]:
        """Stream a deanonymized assistant response.

        Args:
            command (StreamSafeResponseCommand): The streaming request.

        Returns:
            Iterator[str]: Restored chunks that are safe to send to the user.

        Raises:
            ValueError: If strict mode finds a complete unknown placeholder.
        """
        deanonymizer = StreamingDeanonymizer(
            replacements=command.replacements,
            strict=command.strict,
        )

        for chunk in self._assistant_gateway.stream_response(
            command.anonymized_prompt
        ):
            restored_chunk = deanonymizer.push(chunk)
            if restored_chunk:
                yield restored_chunk

        final_chunk = deanonymizer.flush()
        if final_chunk:
            yield final_chunk
