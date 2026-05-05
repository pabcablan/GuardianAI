"""MarkItDown text extractor adapter."""
from __future__ import annotations

from io import BytesIO

from fastapi.concurrency import run_in_threadpool
from markitdown import MarkItDown

from domain.extracted_document import ExtractedDocument
from domain.parsed_document import ParsedDocument
from infrastructure.ports.text_extractor import TextExtractor


class MarkitdownTextExtractor(TextExtractor):
    """Extract text from documents using MarkItDown."""

    def __init__(self) -> None:
        """Initialize the MarkItDown extractor."""
        self.mitd = MarkItDown()

    async def extract_text(self, document: ParsedDocument) -> ExtractedDocument:
        """Extract text from a parsed document.

        Args:
            document (ParsedDocument): The parsed document.

        Returns:
            ExtractedDocument: The document with extracted text.
        """
        return await run_in_threadpool(self._extract_text_sync, document)

    def _extract_text_sync(self, document: ParsedDocument) -> ExtractedDocument:
        """Run the blocking MarkItDown extraction.

        Args:
            document (ParsedDocument): The parsed document.

        Returns:
            ExtractedDocument: The document with extracted text.
        """
        content_bytesio = self.bytes_to_bytesio(document.content)
        mitd_result = self.mitd.convert(content_bytesio)

        return ExtractedDocument(
            document_id=document.document_id,
            filename=document.filename,
            extracted_text=mitd_result.text_content,
        )

    def bytes_to_bytesio(self, content: bytes) -> BytesIO:
        """Convert bytes into a BytesIO object.

        Args:
            content (bytes): The bytes to wrap.

        Returns:
            BytesIO: The wrapped bytes.
        """
        return BytesIO(content)
