"""Track temporary relations between processed documents and messages."""
from __future__ import annotations

from infrastructure.ports.chat_repository_port import ChatRepositoryPort


class ProcessedDocumentRegistry:
    """Store user-message ownership for processed documents.

    The registry keeps a small in-memory cache for the current process, but the
    source of truth is persisted through the chat repository so the relation
    survives restarts.
    """

    def __init__(self, chat_repository: ChatRepositoryPort) -> None:
        self._chat_repository = chat_repository
        self._document_to_message: dict[str, str] = {}

    def remember_user_message(
        self,
        document_id: str,
        user_message_id: str,
    ) -> None:
        """Store the user message that originated a processed document."""
        self._chat_repository.link_document_to_message(
            document_id=document_id,
            message_id=user_message_id,
        )
        self._document_to_message[document_id] = user_message_id

    def get_user_message_id(self, document_id: str) -> str | None:
        """Return the user message linked to one processed document."""
        cached_message_id = self._document_to_message.get(document_id)
        if cached_message_id is not None:
            return cached_message_id

        message_id = self._chat_repository.get_user_message_id_by_document(
            document_id,
        )
        if message_id is not None:
            self._document_to_message[document_id] = message_id

        return message_id
