"""In-memory gateway for chats, messages, and simulated responses."""
from __future__ import annotations

from dataclasses import replace

from application.usecases.create_chat import CreateChatResult
from application.usecases.list_chats import ChatSummary
from application.usecases.load_chat import ChatDetail
from domain.chat import Chat
from domain.message import Message
from infrastructure.ports.internal.chat_repository_port import ChatRepositoryPort


class InMemoryChatGateway(ChatRepositoryPort):
    """Implement chat storage using volatile in-memory state."""

    def __init__(self) -> None:
        """Initialize the in-memory chat store."""
        self._chats: dict[str, Chat] = {}

    def create_chat(self, title: str) -> CreateChatResult:
        """Create a new chat and store it in memory.

        Args:
            title (str): The normalized chat title.

        Returns:
            CreateChatResult: The created chat data.
        """
        chat_id = f"chat-{self._generate_id()}"
        self._chats[chat_id] = Chat(chat_id=chat_id, title=title, messages=[])
        return CreateChatResult(chat_id=chat_id, title=title)

    def list_chats(self) -> list[ChatSummary]:
        """Return summaries for all stored chats.

        Returns:
            list[ChatSummary]: The stored chat summaries.
        """
        summaries: list[ChatSummary] = []
        for chat in self._chats.values():
            summaries.append(
                ChatSummary(
                    chat_id=chat.chat_id,
                    title=chat.title,
                    last_message_preview=chat.last_message_preview(),
                    updated_at=chat.updated_at(),
                )
            )
        return summaries

    def load_chat(self, chat_id: str) -> ChatDetail | None:
        """Return a copied chat to avoid external mutations.

        Args:
            chat_id (str): The identifier of the chat to load.

        Returns:
            ChatDetail | None: The copied chat, or None when it does not exist.
        """
        chat = self._chats.get(chat_id)
        if chat is None:
            return None

        return replace(chat, messages=[replace(message) for message in chat.messages])

    def delete_chat(self, chat_id: str) -> None:
        """Delete a chat when it exists.

        Args:
            chat_id (str): The identifier of the chat to delete.
        """
        self._chats.pop(chat_id, None)

    def rename_chat(self, chat_id: str, title: str) -> None:
        """Update the title of an existing chat.

        Args:
            chat_id (str): The identifier of the chat to rename.
            title (str): The normalized chat title.

        Raises:
            KeyError: If the target chat does not exist.
        """
        chat = self._require_chat(chat_id)
        chat.rename(title)

    def append_message(self, chat_id: str, message: Message) -> None:
        """Append one message to an existing chat.

        Args:
            chat_id (str): The identifier of the chat to update.
            message (Message): The message to append.
        """
        chat = self._require_chat(chat_id)
        chat.add_message(message)

    def update_message_anonymized_content(
        self,
        message_id: str,
        anonymized_content: str,
    ) -> None:
        """Store the anonymized content in an existing user message.

        Args:
            message_id (str): The message identifier.
            anonymized_content (str): The anonymized message content.

        Raises:
            KeyError: If the message does not exist.
        """
        for chat in self._chats.values():
            for index, message in enumerate(chat.messages):
                if message.message_id == message_id:
                    chat.messages[index] = replace(
                        message,
                        anonymized_content=anonymized_content,
                    )
                    return

        raise KeyError(message_id)

    def _require_chat(self, chat_id: str) -> Chat:
        """Return a chat or raise when it is not registered.

        Args:
            chat_id (str): The identifier of the chat to retrieve.

        Returns:
            Chat: The stored chat.

        Raises:
            KeyError: If the target chat does not exist.
        """
        chat = self._chats.get(chat_id)
        if chat is None:
            raise KeyError(chat_id)
        return chat

    def _generate_id(self) -> str:
        """Generate a unique identifier suffix.

        Returns:
            str: A UUID-based hexadecimal identifier.
        """
        from uuid import uuid4

        return uuid4().hex
