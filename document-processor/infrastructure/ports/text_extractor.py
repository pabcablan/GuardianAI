"""
Defines the contract for a document text extractor.
Its responsible for extracting the text content from a parsed document
and returning an ExtractedDocument object
"""

from typing import Protocol

from domain.parsed_document import ParsedDocument
from domain.extracted_document import ExtractedDocument

class TextExtractor(Protocol):
    async def extract_text(self, document: ParsedDocument) -> ExtractedDocument:
        ...