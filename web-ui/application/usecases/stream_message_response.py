"""Use case for streaming safe responses to user chat messages."""
from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from infrastructure.ports.external.privacy_shield_port import (
    PrivacyShieldMessageStreamRequest,
    PrivacyShieldPort,
    PrivacyShieldStreamEvent,
)


@dataclass(frozen=True)
class StreamMessageResponseCommand:
    """Represent the input required to stream a chat message response.

    Attributes:
        chat_id (str): The chat that will display the response.
        content (str): The user message content.
    """

    chat_id: str
    content: str


class StreamMessageResponseUseCase:
    """Consume a safe streamed answer for a user chat message."""

    def __init__(self, privacy_shield: PrivacyShieldPort) -> None:
        """Initialize the use case.

        Args:
            privacy_shield (PrivacyShieldPort): The privacy-shield gateway.
        """
        self._privacy_shield = privacy_shield

    def execute(
        self,
        command: StreamMessageResponseCommand,
    ) -> Iterator[PrivacyShieldStreamEvent]:
        """Stream safe response events for a user message.

        Args:
            command (StreamMessageResponseCommand): The stream request data.

        Returns:
            Iterator[PrivacyShieldStreamEvent]: Safe stream events.

        Raises:
            ValueError: If the chat identifier or message content is empty.
        """
        content = command.content.strip()
        if not command.chat_id.strip():
            raise ValueError("Chat id cannot be empty.")
        if not content:
            raise ValueError("Message content cannot be empty.")

        return self._privacy_shield.stream_message_response(
            PrivacyShieldMessageStreamRequest(
                chat_id=command.chat_id,
                content=content,
            )
        )
