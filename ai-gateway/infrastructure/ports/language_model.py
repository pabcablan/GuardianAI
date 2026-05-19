"""Port for streaming responses from one language model provider."""
from __future__ import annotations

from collections.abc import AsyncGenerator
from abc import ABC, abstractmethod

from domain.value_objects.message import Message


class LanguageModel(ABC):
    """Define the provider streaming contract used by ai-gateway."""

    @abstractmethod
    async def stream(
        self,
        messages: list[Message],
        model: str,
    ) -> AsyncGenerator[str, None]:
        """Stream text chunks from the configured provider.

        Args:
            messages (list[Message]): The normalized conversation messages.
            model (str): The provider model identifier.

        Returns:
            AsyncGenerator[str, None]: The streamed response chunks.
        """
        ...
