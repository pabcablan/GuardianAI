from __future__ import annotations

from dataclasses import dataclass

from domain.document import (
    ExtractedDocument,
    ExtractionProgressCallback,
    ProcessingDocument,
)
from infrastructure.ports.internal.document_extractor_port import (
    DocumentExtractorPort,
)


@dataclass(frozen=True)
class ExtractDocumentCommand:
    filename: str
    content_type: str
    content: bytes


@dataclass(frozen=True)
class ExtractDocumentResult:
    document_id: str
    filename: str
    extracted_text: str
    page_count: int


class ExtractDocumentUseCase:
    def __init__(self, extractor: DocumentExtractorPort) -> None:
        self._extractor = extractor

    def execute(
        self,
        command: ExtractDocumentCommand,
        *,
        progress_callback: ExtractionProgressCallback | None = None,
    ) -> ExtractDocumentResult:
        document = ProcessingDocument(
            filename=command.filename,
            content_type=command.content_type,
            content=command.content,
        )
        extracted = self._extractor.extract_document(
            document,
            progress_callback=progress_callback,
        )
        return self._to_result(extracted)

    def _to_result(self, extracted: ExtractedDocument) -> ExtractDocumentResult:
        return ExtractDocumentResult(
            document_id=extracted.document_id,
            filename=extracted.filename,
            extracted_text=extracted.extracted_text,
            page_count=extracted.page_count,
        )
