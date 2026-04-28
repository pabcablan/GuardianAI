"""Use case for retrieving response chunks."""
from __future__ import annotations

from dataclasses import dataclass

from infrastructure.ports.internal.stream_service_port import StreamServicePort


@dataclass(frozen=True)
class StreamResponseCommand:
    """Represent the input required to request response chunks.

    Attributes:
        chat_id (str): The identifier of the chat that owns the response.
    """

    chat_id: str

class StreamResponseUseCase:
    """Retrieve chunks associated with the latest assistant response."""

    def __init__(self, gateway: StreamServicePort) -> None:
        """Initialize the use case.

        Args:
            gateway (StreamServicePort): The response stream gateway.
        """
        self._gateway = gateway

    def execute(self, command: StreamResponseCommand) -> list[str]:
        """Return the response chunks for a chat.

        Args:
            command (StreamResponseCommand): The response stream request data.

        Returns:
            list[str]: The available response chunks.

        Raises:
            ValueError: If the chat identifier is empty.
        """
        if not command.chat_id.strip():
            raise ValueError("Chat id cannot be empty.")

        return self._gateway.stream_response(command.chat_id)
