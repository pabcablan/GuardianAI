from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from application.usecases.attach_document import AttachDocumentResult


class DocumentServicePort(Protocol):
    def attach_document(
        self,
        chat_id: str,
        filename: str,
        content_type: str,
        content: bytes,
    ) -> "AttachDocumentResult":
        """Attach a PDF document to a chat conversation."""
