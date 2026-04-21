from __future__ import annotations

from typing import Protocol


class StreamServicePort(Protocol):
    def stream_response(self, chat_id: str) -> list[str]:
        """Return the response chunks associated with a conversation."""
