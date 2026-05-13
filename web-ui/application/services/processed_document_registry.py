"""Track temporary relations between processed documents and messages."""
from __future__ import annotations


class ProcessedDocumentRegistry:
    """Store user-message ownership for processed documents."""

    def __init__(self) -> None:
        self._document_to_message: dict[str, str] = {}

    def remember_user_message(
        self,
        document_id: str,
        user_message_id: str,
    ) -> None:
        """Store the user message that originated a processed document."""
        self._document_to_message[document_id] = user_message_id

    def get_user_message_id(self, document_id: str) -> str | None:
        """Return the user message linked to one processed document."""
        return self._document_to_message.get(document_id)
