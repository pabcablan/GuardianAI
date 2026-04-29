"""Use case for renaming chat conversations."""
from __future__ import annotations

from dataclasses import dataclass

from infrastructure.ports.internal.chat_repository_port import ChatRepositoryPort


@dataclass(frozen=True)
class RenameChatCommand:
    """Represent the input required to rename a chat.

    Attributes:
        chat_id (str): The identifier of the chat to rename.
        title (str): The requested new title.
    """

    chat_id: str
    title: str

class RenameChatUseCase:
    """Validate and apply chat title changes."""

    def __init__(self, gateway: ChatRepositoryPort) -> None:
        """Initialize the use case.

        Args:
            gateway (ChatRepositoryPort): The chat repository gateway.
        """
        self._gateway = gateway

    def execute(self, command: RenameChatCommand) -> None:
        """Rename the requested chat.

        Args:
            command (RenameChatCommand): The rename request data.

        Raises:
            ValueError: If the chat identifier or title is empty.
        """
        title = command.title.strip()
        if not command.chat_id.strip():
            raise ValueError("Chat id cannot be empty.")
        if not title:
            raise ValueError("Chat title cannot be empty.")

        self._gateway.rename_chat(command.chat_id, title)
