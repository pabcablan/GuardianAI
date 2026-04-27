from typing import Protocol

from domain.document import ExtractedDocument, ExtractionProgressCallback, ProcessingDocument


class DocumentExtractorPort(Protocol):
    def extract_document(self, document: ProcessingDocument,
        progress_callback: ExtractionProgressCallback \
        | None = None) -> ExtractedDocument:
        """Extract text content from a supported document."""
