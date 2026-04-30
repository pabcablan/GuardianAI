"""Internal port for attaching documents to chat conversations."""
from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from application.usecases.attach_document import AttachDocumentStreamEvent


class DocumentServicePort(Protocol):
    """Define the document operations required by document use cases."""

    def stream_attach_document(
        self,
        chat_id: str,
        filename: str,
        content_type: str,
        content: bytes,
        prompt: str = "",
    ) -> Iterator["AttachDocumentStreamEvent"]:
        """Attach a PDF document while streaming processing updates.

        Args:
            chat_id (str): The identifier of the chat that receives the document.
            filename (str): The document filename.
            content_type (str): The document MIME type.
            content (bytes): The document bytes.
            prompt (str): The optional prompt to combine with the document text.

        Returns:
            Iterator[AttachDocumentStreamEvent]: The document attachment events.
        """
