"""Internal port for persisting and querying chat conversations."""
from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from domain.chat import Chat
from domain.message import Message

if TYPE_CHECKING:
    from application.usecases.create_chat import CreateChatResult
    from application.usecases.list_chats import ChatSummary


class ChatRepositoryPort(Protocol):
    """Define the chat storage operations required by use cases."""

    def create_chat(self, title: str) -> "CreateChatResult":
        """Create and persist a new chat conversation.

        Args:
            title (str): The normalized chat title.

        Returns:
            CreateChatResult: The created chat data.
        """

    def list_chats(self) -> list["ChatSummary"]:
        """Return the chat summaries shown in the sidebar.

        Returns:
            list[ChatSummary]: The stored chat summaries.
        """

    def load_chat(self, chat_id: str) -> Chat | None:
        """Return the full chat detail for a given conversation.

        Args:
            chat_id (str): The identifier of the chat to load.

        Returns:
            Chat | None: The chat detail, or None when it does not exist.
        """

    def delete_chat(self, chat_id: str) -> None:
        """Remove a conversation from storage.

        Args:
            chat_id (str): The identifier of the chat to remove.
        """

    def rename_chat(self, chat_id: str, title: str) -> None:
        """Update the title of an existing conversation.

        Args:
            chat_id (str): The identifier of the chat to rename.
            title (str): The normalized chat title.
        """

    def append_message(self, chat_id: str, message: Message) -> None:
        """Append one message to a chat.

        Args:
            chat_id (str): The identifier of the chat that owns the message.
            message (Message): The message to persist.
        """

    def update_message_anonymized_content(
        self,
        message_id: str,
        anonymized_content: str,
    ) -> None:
        """Store the anonymized version of a user message.

        Args:
            message_id (str): The message identifier.
            anonymized_content (str): The anonymized message content.
        """
