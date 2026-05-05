"""Use case for processing uploaded documents."""
from __future__ import annotations

from typing import Any

from infrastructure.ports.document_parser import DocumentParser
from infrastructure.ports.text_extractor import TextExtractor


class ProcessDocument:
    """Parse a document and extract its text."""

    def __init__(
        self,
        parser: DocumentParser,
        text_extractor: TextExtractor,
    ) -> None:
        """Initialize the use case.

        Args:
            parser (DocumentParser): The document parser.
            text_extractor (TextExtractor): The text extractor.
        """
        self._parser = parser
        self._text_extractor = text_extractor

    async def execute(self, document: Any) -> str:
        """Process an uploaded document.

        Args:
            document (Any): The uploaded document object.

        Returns:
            str: The extracted document text.
        """
        parsed_doc = await self._parser.parse(document)
        extracted_doc = await self._text_extractor.extract_text(parsed_doc)
        return extracted_doc.extracted_text
