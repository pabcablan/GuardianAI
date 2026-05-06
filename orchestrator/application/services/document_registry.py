"""In-memory registry for processed document data."""
from __future__ import annotations

from domain.processed_document import ProcessedDocumentContext


class DocumentRegistry:
    """Store processed document context during an orchestrator process lifetime."""

    def __init__(self) -> None:
        """Initialize the in-memory registry."""
        self._documents: dict[str, ProcessedDocumentContext] = {}

    def store(self, document_id: str, document: ProcessedDocumentContext) -> None:
        """Store one processed document context.

        Args:
            document_id (str): The processed document identifier.
            document (ProcessedDocumentContext): The document context to store.
        """
        self._documents[document_id] = document

    def get(self, document_id: str) -> ProcessedDocumentContext:
        """Return a processed document context.

        Args:
            document_id (str): The processed document identifier.

        Returns:
            ProcessedDocumentContext: The stored document context.

        Raises:
            KeyError: If the document is unknown.
        """
        return self._documents[document_id]
