from typing import Any

from domain.extracted_document import ExtractedDocument
from infrastructure.ports.document_parser import DocumentParser
from infrastructure.ports.text_extractor import TextExtractor


class ProcessDocument:
    """Coordinate parsing and text extraction for an uploaded document."""

    def __init__(
        self,
        parser: DocumentParser,
        text_extractor: TextExtractor,
    ) -> None:
        self._parser = parser
        self._text_extractor = text_extractor

    async def execute(self, document: Any) -> ExtractedDocument:
        """Parse the incoming document and extract its text.

        Args:
            document (Any): Uploaded file or equivalent external document input.

        Returns:
            ExtractedDocument: Extracted text and document metadata.
        """
        parsed_doc = await self._parser.parse(document)
        return await self._text_extractor.extract_text(parsed_doc)
