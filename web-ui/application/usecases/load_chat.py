"""Use case for loading a chat conversation."""
from __future__ import annotations

from domain.chat import Chat as ChatDetail
from infrastructure.ports.internal.chat_repository_port import ChatRepositoryPort


class LoadChatUseCase:
    """Retrieve the full history of a chat."""

    def __init__(self, gateway: ChatRepositoryPort) -> None:
        """Initialize the use case.

        Args:
            gateway (ChatRepositoryPort): The chat repository gateway.
        """
        self._gateway = gateway

    def execute(self, chat_id: str) -> ChatDetail | None:
        """Load a chat by identifier.

        Args:
            chat_id (str): The identifier of the chat to load.

        Returns:
            ChatDetail | None: The chat detail, or None when it does not exist.
        """
        return self._gateway.load_chat(chat_id)
