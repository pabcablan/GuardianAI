import logging

from infrastructure.ports.text_extractor import TextExtractor
from domain.parsed_document import ParsedDocument
from domain.extracted_document import ExtractedDocument

logger = logging.getLogger(__name__)

class FallbackTextExtractor:
    def __init__(self, primary: TextExtractor, fallback: TextExtractor, min_chars: int = 25):
        self._primary = primary
        self._fallback = fallback
        self._min_chars = min_chars

    async def extract_text(self, document: ParsedDocument) -> ExtractedDocument:
        try:
            result = await self._primary.extract_text(document)
            if self.not_enough_text(result):
                logger.warning(f"Primary extractor returned insufficient text. Using fallback. Extracted text length: {len(result.extracted_text)}")
                return await self._fallback.extract_text(document)
            return result
        
        except Exception as e:
            logger.warning(f"Primary extractor failed: {e}. Falling back to LLM.")
            return await self._fallback.extract_text(document)
        
    def not_enough_text(self, extracted: ExtractedDocument) -> bool:
        return len(extracted.extracted_text.strip()) < self._min_chars
