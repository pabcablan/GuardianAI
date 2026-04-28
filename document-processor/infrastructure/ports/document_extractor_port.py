from typing import Protocol

from domain.extracted_document import ExtractedDocument
from domain.extraction_progress import ExtractionProgressCallback
from domain.processing_document import ProcessingDocument


class DocumentExtractorPort(Protocol):
    def extract_document(self, document: ProcessingDocument,
        progress_callback: ExtractionProgressCallback | None = None) -> ExtractedDocument:
        """Extract text content from a supported document."""
