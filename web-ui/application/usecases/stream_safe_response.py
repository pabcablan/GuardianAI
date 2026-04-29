"""Use case for streaming safe responses from privacy-shield."""
from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from infrastructure.ports.external.privacy_shield_port import (
    PrivacyShieldPort,
    PrivacyShieldStreamEvent,
    PrivacyShieldStreamRequest,
)


@dataclass(frozen=True)
class StreamSafeResponseCommand:
    """Represent the input required to request a safe response stream.

    Attributes:
        chat_id (str): The chat that will display the stream.
        document_id (str): The processed document associated with the stream.
    """

    chat_id: str
    document_id: str


class StreamSafeResponseUseCase:
    """Consume a safe response stream exposed by privacy-shield."""

    def __init__(self, privacy_shield: PrivacyShieldPort) -> None:
        """Initialize the use case.

        Args:
            privacy_shield (PrivacyShieldPort): The privacy-shield gateway.
        """
        self._privacy_shield = privacy_shield

    def execute(
        self,
        command: StreamSafeResponseCommand,
    ) -> Iterator[PrivacyShieldStreamEvent]:
        """Stream safe response events for a processed document.

        Args:
            command (StreamSafeResponseCommand): The stream request data.

        Returns:
            Iterator[PrivacyShieldStreamEvent]: Safe stream events.

        Raises:
            ValueError: If the chat or document identifier is empty.
        """
        if not command.chat_id.strip():
            raise ValueError("Chat id cannot be empty.")
        if not command.document_id.strip():
            raise ValueError("Document id cannot be empty.")

        return self._privacy_shield.stream_safe_response(
            PrivacyShieldStreamRequest(
                chat_id=command.chat_id,
                document_id=command.document_id,
            )
        )
