from typing import Protocol

from domain.parsed_document import ParsedDocument
from domain.extracted_document import ExtractedDocument

class TextExtractor(Protocol):
    async def extract_text(self, document: ParsedDocument) -> ExtractedDocument:
        ...