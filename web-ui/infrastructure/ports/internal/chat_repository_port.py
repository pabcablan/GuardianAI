from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from domain.chat import Chat

if TYPE_CHECKING:
    from application.usecases.create_chat import CreateChatResult
    from application.usecases.list_chats import ChatSummary


class ChatRepositoryPort(Protocol):
    def create_chat(self, title: str) -> "CreateChatResult":
        """Create and persist a new chat conversation."""

    def list_chats(self) -> list["ChatSummary"]:
        """Return the chat summaries shown in the sidebar."""

    def load_chat(self, chat_id: str) -> Chat | None:
        """Return the full chat detail for a given conversation."""

    def delete_chat(self, chat_id: str) -> None:
        """Remove a conversation from storage."""

    def rename_chat(self, chat_id: str, title: str) -> None:
        """Update the title of an existing conversation."""
