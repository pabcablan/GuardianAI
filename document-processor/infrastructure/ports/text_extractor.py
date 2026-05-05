"""Port that defines document text extraction."""
from __future__ import annotations

from typing import Protocol

from domain.extracted_document import ExtractedDocument
from domain.parsed_document import ParsedDocument


class TextExtractor(Protocol):
    """Define the contract for text extractors."""

    async def extract_text(self, document: ParsedDocument) -> ExtractedDocument:
        """Extract text from a parsed document.

        Args:
            document (ParsedDocument): The parsed document to inspect.

        Returns:
            ExtractedDocument: The document with extracted text.
        """
        ...
