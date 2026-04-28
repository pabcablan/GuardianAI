"""Internal port for querying response chunks."""
from __future__ import annotations

from typing import Protocol


class StreamServicePort(Protocol):
    """Define response chunk retrieval operations."""

    def stream_response(self, chat_id: str) -> list[str]:
        """Return the response chunks associated with a conversation.

        Args:
            chat_id (str): The identifier of the chat.

        Returns:
            list[str]: The response chunks associated with the chat.
        """
