"""Internal port for persisting and querying chat conversations."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from domain.chat import Chat
from domain.message import Message

if TYPE_CHECKING:
    from application.usecases.create_chat import CreateChatResult
    from application.usecases.list_chats import ChatSummary


class ChatRepositoryPort(ABC):
    """Define the chat storage operations required by use cases."""

    @abstractmethod
    def create_chat(self, title: str) -> "CreateChatResult":
        """Create and persist a new chat conversation."""
        ...

    @abstractmethod
    def list_chats(self) -> list["ChatSummary"]:
        """Return the chat summaries shown in the sidebar."""
        ...

    @abstractmethod
    def load_chat(self, chat_id: str) -> Chat | None:
        """Return the full chat detail for a given conversation."""
        ...

    @abstractmethod
    def delete_chat(self, chat_id: str) -> None:
        """Remove a conversation from storage."""
        ...

    @abstractmethod
    def rename_chat(self, chat_id: str, title: str) -> None:
        """Update the title of an existing conversation."""
        ...

    @abstractmethod
    def append_message(self, chat_id: str, message: Message) -> None:
        """Append one message to a chat."""
        ...

    @abstractmethod
    def update_message_anonymized_content(
        self,
        message_id: str,
        anonymized_content: str,
        anonymization_replacements: dict[str, str] | None = None,
    ) -> None:
        """Store the anonymized version of a user message."""
        ...

    @abstractmethod
    def link_document_to_message(
        self,
        document_id: str,
        message_id: str,
    ) -> None:
        """Persist the processed document linked to one user message."""
        ...

    @abstractmethod
    def get_user_message_id_by_document(
        self,
        document_id: str,
    ) -> str | None:
        """Return the user message linked to one processed document."""
        ...

    @abstractmethod
    def get_chat_replacements(self, chat_id: str) -> dict[str, str]:
        """Return all anonymization replacements stored for a chat."""
        ...
