from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from application.usecases.attach_document import AttachDocumentStreamEvent


class DocumentServicePort(Protocol):
    def stream_attach_document(
        self,
        chat_id: str,
        filename: str,
        content_type: str,
        content: bytes,
    ) -> Iterator["AttachDocumentStreamEvent"]:
        """Attach a PDF document while streaming processing updates."""
