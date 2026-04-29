"""Use case for deleting chat conversations."""
from __future__ import annotations

from infrastructure.ports.internal.chat_repository_port import ChatRepositoryPort


class DeleteChatUseCase:
    """Delete an existing chat by its identifier."""

    def __init__(self, gateway: ChatRepositoryPort) -> None:
        """Initialize the use case.

        Args:
            gateway (ChatRepositoryPort): The chat repository gateway.
        """
        self._gateway = gateway

    def execute(self, chat_id: str) -> None:
        """Delete the requested chat.

        Args:
            chat_id (str): The identifier of the chat to delete.

        Raises:
            ValueError: If the chat identifier is empty.
        """
        if not chat_id.strip():
            raise ValueError("Chat id cannot be empty.")

        self._gateway.delete_chat(chat_id)
