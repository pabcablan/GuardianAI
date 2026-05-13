"""Use case for streaming safe responses to user chat messages."""
from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from infrastructure.ports.external.orchestrator_response_port import (
    OrchestratorChatHistoryMessage,
    OrchestratorMessageResponseRequest,
    OrchestratorResponsePort,
    OrchestratorStreamEvent,
)


@dataclass(frozen=True)
class StreamMessageResponseCommand:
    """Represent the input required to stream a chat message response.

    Attributes:
        chat_id (str): The chat that will display the response.
        content (str): The user message content.
        model (str): The AI model selected by the user.
        history (list[OrchestratorChatHistoryMessage]): Previous anonymized
            conversation messages.
    """

    chat_id: str
    content: str
    model: str
    history: list[OrchestratorChatHistoryMessage]
    settings: dict[str, str]


class StreamMessageResponseUseCase:
    """Consume a safe streamed answer for a user chat message."""

    def __init__(self, orchestrator: OrchestratorResponsePort) -> None:
        """Initialize the use case.

        Args:
            orchestrator (OrchestratorResponsePort): The orchestrator gateway.
        """
        self._orchestrator = orchestrator

    def execute(
        self,
        command: StreamMessageResponseCommand,
    ) -> Iterator[OrchestratorStreamEvent]:
        """Stream safe response events for a user message.

        Args:
            command (StreamMessageResponseCommand): The stream request data.

        Returns:
            Iterator[OrchestratorStreamEvent]: Safe stream events.

        Raises:
            ValueError: If the chat identifier or message content is empty.
        """
        content = command.content.strip()
        model = command.model
        if not command.chat_id.strip():
            raise ValueError("Chat id cannot be empty.")
        if not content:
            raise ValueError("Message content cannot be empty.")

        return self._orchestrator.stream_message_response(
            OrchestratorMessageResponseRequest(
                chat_id=command.chat_id,
                content=content,
                model=model,
                history=command.history,
                settings=command.settings,
            )
        )
