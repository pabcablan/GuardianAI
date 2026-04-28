"""Internal port for sending messages to the assistant."""
from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from application.usecases.send_message import SendMessageResult


class MessageServicePort(Protocol):
    """Define the message operations required by message use cases."""

    def send_message(
        self,
        chat_id: str,
        content: str,
    ) -> "SendMessageResult":
        """Send a prompt and return the assistant response payload.

        Args:
            chat_id (str): The identifier of the target chat.
            content (str): The normalized user message content.

        Returns:
            SendMessageResult: The generated message identifiers and response.
        """
