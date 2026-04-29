"""Use case for listing available chat conversations."""
from __future__ import annotations

from dataclasses import dataclass

from infrastructure.ports.internal.chat_repository_port import ChatRepositoryPort


@dataclass(frozen=True)
class ChatSummary:
    """Represent a chat summary shown in chat lists.

    Attributes:
        chat_id (str): The chat identifier.
        title (str): The chat title.
        last_message_preview (str): The preview of the last message.
        updated_at (str): The timestamp displayed for the chat.
    """

    chat_id: str
    title: str
    last_message_preview: str
    updated_at: str

class ListChatsUseCase:
    """Retrieve stored chat summaries."""

    def __init__(self, gateway: ChatRepositoryPort) -> None:
        """Initialize the use case.

        Args:
            gateway (ChatRepositoryPort): The chat repository gateway.
        """
        self._gateway = gateway

    def execute(self) -> list[ChatSummary]:
        """List all available chats.

        Returns:
            list[ChatSummary]: The available chat summaries.
        """
        return self._gateway.list_chats()
