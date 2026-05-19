from abc import ABC, abstractmethod

from domain.extracted_document import ExtractedDocument
from domain.parsed_document import ParsedDocument


class TextExtractor(ABC):
    """Contract for components that extract text from parsed documents."""

    @abstractmethod
    async def extract_text(self, document: ParsedDocument) -> ExtractedDocument:
        """Extract text content from a parsed document.

        Args:
            document (ParsedDocument): Parsed document with metadata and bytes.

        Returns:
            ExtractedDocument: Extracted text plus document metadata.
        """
        ...
