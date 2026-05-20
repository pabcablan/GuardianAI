"""Internal port for attaching documents to chat conversations."""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from application.usecases.attach_document import AttachDocumentStreamEvent


class DocumentServicePort(ABC):
    """Define the document operations required by document use cases."""

    @abstractmethod
    def stream_attach_document(
        self,
        chat_id: str,
        filename: str,
        content_type: str,
        content: bytes,
        prompt: str = "",
    ) -> Iterator["AttachDocumentStreamEvent"]:
        """Attach a PDF document while streaming processing updates."""
        ...
