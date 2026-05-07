from typing import Any

from infrastructure.ports.document_parser import DocumentParser
from infrastructure.ports.text_extractor import TextExtractor

class ProcessDocument:
    def __init__(self, parser: DocumentParser, text_extractor: TextExtractor):
        self._parser = parser
        self._text_extractor = text_extractor

    #TODO add exception handling
    async def execute(self, document: Any) -> str:

        parsed_doc = await self._parser.parse(document)
        extracted_doc = await self._text_extractor.extract_text(parsed_doc)
                
        return extracted_doc.extracted_text