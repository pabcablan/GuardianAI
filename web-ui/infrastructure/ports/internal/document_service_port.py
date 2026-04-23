from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from application.usecases.attach_document import (
        AttachDocumentResult,
        AttachDocumentStreamEvent,
    )


class DocumentServicePort(Protocol):
    def attach_document(
        self,
        chat_id: str,
        filename: str,
        content_type: str,
        content: bytes,
    ) -> "AttachDocumentResult":
        """Attach a PDF document to a chat conversation."""

    def stream_attach_document(
        self,
        chat_id: str,
        filename: str,
        content_type: str,
        content: bytes,
    ) -> Iterator["AttachDocumentStreamEvent"]:
        """Attach a PDF document while streaming processing updates."""
