from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from application.usecases.send_message import SendMessageResult


class MessageServicePort(Protocol):
    def send_message(
        self,
        chat_id: str,
        content: str,
    ) -> "SendMessageResult":
        """Send a prompt and return the assistant response payload."""
