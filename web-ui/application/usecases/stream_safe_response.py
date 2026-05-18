"""Use case for streaming safe responses from orchestrator."""
from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from infrastructure.ports.external.orchestrator_response_port import (
    OrchestratorDocumentResponseRequest,
    OrchestratorResponsePort,
    OrchestratorStreamEvent,
)


@dataclass(frozen=True)
class StreamSafeResponseCommand:
    """Represent the input required to request a safe response stream.

    Attributes:
        chat_id (str): The chat that will display the stream.
        document_id (str): The processed document associated with the stream.
        model (str): The AI model selected by the user.
    """

    chat_id: str
    document_id: str
    model: str
    settings: dict[str, str]
    replacements: dict[str, str]


class StreamSafeResponseUseCase:
    """Consume a safe response stream exposed by orchestrator."""

    def __init__(self, orchestrator: OrchestratorResponsePort) -> None:
        """Initialize the use case.

        Args:
            orchestrator (OrchestratorResponsePort): The orchestrator gateway.
        """
        self._orchestrator = orchestrator

    def execute(
        self,
        command: StreamSafeResponseCommand,
    ) -> Iterator[OrchestratorStreamEvent]:
        """Stream safe response events for a processed document.

        Args:
            command (StreamSafeResponseCommand): The stream request data.

        Returns:
            Iterator[OrchestratorStreamEvent]: Safe stream events.

        Raises:
            ValueError: If the chat or document identifier is empty.
        """
        if not command.chat_id.strip():
            raise ValueError("Chat id cannot be empty.")
        if not command.document_id.strip():
            raise ValueError("Document id cannot be empty.")

        return self._orchestrator.stream_safe_response(
            OrchestratorDocumentResponseRequest(
                chat_id=command.chat_id,
                document_id=command.document_id,
                model=command.model,
                settings=command.settings,
                replacements=command.replacements,
            )
        )
