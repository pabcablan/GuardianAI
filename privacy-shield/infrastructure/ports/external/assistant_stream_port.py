"""Port for obtaining streamed anonymized assistant responses."""
from __future__ import annotations

from collections.abc import Iterator
from typing import Protocol


class AssistantStreamPort(Protocol):
    """Define how privacy-shield obtains assistant response streams."""

    def stream_response(self, prompt: str) -> Iterator[str]:
        """Stream an assistant response for an anonymized prompt.

        Args:
            prompt (str): The anonymized prompt sent to the assistant service.

        Returns:
            Iterator[str]: The anonymized response chunks.
        """
