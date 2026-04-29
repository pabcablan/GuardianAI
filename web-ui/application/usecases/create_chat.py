"""Use case for creating new chat conversations."""
from __future__ import annotations

from dataclasses import dataclass

from infrastructure.ports.internal.chat_repository_port import ChatRepositoryPort


@dataclass(frozen=True)
class CreateChatCommand:
    """Represent the input required to create a chat.

    Attributes:
        title (str | None): The optional title requested by the user.
    """

    title: str | None = None


@dataclass(frozen=True)
class CreateChatResult:
    """Represent the result returned after creating a chat.

    Attributes:
        chat_id (str): The generated chat identifier.
        title (str): The normalized chat title.
    """

    chat_id: str
    title: str

class CreateChatUseCase:
    """Create chats and apply the default title when needed."""

    def __init__(self, gateway: ChatRepositoryPort) -> None:
        """Initialize the use case.

        Args:
            gateway (ChatRepositoryPort): The chat repository gateway.
        """
        self._gateway = gateway

    def execute(self, command: CreateChatCommand) -> CreateChatResult:
        """Create a chat from the given command.

        Args:
            command (CreateChatCommand): The chat creation input.

        Returns:
            CreateChatResult: The created chat data.
        """
        title = (command.title or "Nuevo chat").strip() or "Nuevo chat"
        return self._gateway.create_chat(title)
