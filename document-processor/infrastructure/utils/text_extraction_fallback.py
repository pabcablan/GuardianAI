import logging
from inspect import isawaitable

from infrastructure.ports.text_extractor import TextExtractor
from domain.parsed_document import ParsedDocument
from domain.extracted_document import ExtractedDocument

logger = logging.getLogger(__name__)


class FallbackTextExtractor:
    def __init__(
        self,
        primary: TextExtractor,
        fallback: TextExtractor,
        min_chars: int = 25,
    ):
        self._primary = primary
        self._fallback = fallback
        self._min_chars = min_chars

    async def extract_text(self, document: ParsedDocument) -> ExtractedDocument:
        try:
            result = await self._extract_with(self._primary, document)
            if self.not_enough_text(result):
                logger.warning(
                    "Primary extractor returned insufficient text. "
                    "Using fallback. Extracted text length: "
                    f"{len(result.extracted_text)}"
                )
                return await self._extract_with(self._fallback, document)
            return result

        except Exception as e:
            logger.warning(f"Primary extractor failed: {e}. Falling back to LLM.")
            return await self._extract_with(self._fallback, document)

    async def _extract_with(
        self,
        extractor: TextExtractor,
        document: ParsedDocument,
    ) -> ExtractedDocument:
        result = extractor.extract_text(document)
        if isawaitable(result):
            return await result

        return result

    def not_enough_text(self, extracted: ExtractedDocument) -> bool:
        return len(extracted.extracted_text.strip()) < self._min_chars
