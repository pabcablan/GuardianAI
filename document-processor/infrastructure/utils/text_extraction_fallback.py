import logging

from domain.extracted_document import ExtractedDocument
from domain.parsed_document import ParsedDocument
from infrastructure.ports.text_extractor import TextExtractor


LOGGER = logging.getLogger(__name__)


class FallbackTextExtractor(TextExtractor):
    """Try a primary extractor first and fall back when output is too weak."""

    def __init__(
        self,
        primary: TextExtractor,
        fallback: TextExtractor,
        min_chars: int = 25,
    ) -> None:
        self._primary = primary
        self._fallback = fallback
        self._min_chars = min_chars

    async def extract_text(self, document: ParsedDocument) -> ExtractedDocument:
        """Extract text using a primary extractor with a fallback strategy.

        Args:
            document (ParsedDocument): Parsed document bytes and metadata.

        Returns:
            ExtractedDocument: Extracted text plus document metadata.
        """
        try:
            result = await self._extract_with(self._primary, document)
            if self._has_insufficient_text(result):
                LOGGER.warning(
                    "Primary extractor returned insufficient text. "
                    "Using fallback. Extracted text length: "
                    f"{len(result.extracted_text)}"
                )
                return await self._extract_with(self._fallback, document)
            return result

        except Exception as error:
            LOGGER.warning(
                "Primary extractor failed: %s. Falling back to LLM.",
                error,
            )
            return await self._extract_with(self._fallback, document)

    async def _extract_with(
        self,
        extractor: TextExtractor,
        document: ParsedDocument,
    ) -> ExtractedDocument:
        """Run one extractor implementation for the given document."""
        return await extractor.extract_text(document)

    def _has_insufficient_text(self, extracted: ExtractedDocument) -> bool:
        """Return whether the extracted text is too short to trust."""
        return len(extracted.extracted_text.strip()) < self._min_chars
