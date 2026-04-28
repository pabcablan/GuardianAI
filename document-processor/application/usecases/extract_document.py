from dataclasses import dataclass

from domain.extracted_document import ExtractedDocument
from domain.extraction_progress import ExtractionProgressCallback
from domain.processing_document import ProcessingDocument
from infrastructure.ports.internal.document_extractor_port import DocumentExtractorPort


@dataclass(frozen=True)
class ExtractDocumentCommand: #TODO should this go in domain?
    filename: str
    content_type: str
    content: bytes


@dataclass(frozen=True)
class ExtractDocumentResult: #TODO should also this go in domain?
    document_id: str
    filename: str
    extracted_text: str
    page_count: int


class ExtractDocumentUseCase:
    def __init__(self, extractor: DocumentExtractorPort) -> None:
        self._extractor = extractor
                                                                        #TODO add exception handling
    def execute(self, command: ExtractDocumentCommand,                  #TODO should this me async? 
                progress_callback: ExtractionProgressCallback \
                | None = None) -> ExtractDocumentResult:
        
        document = ProcessingDocument(command.filename,
                                      command.content_type,
                                      command.content)
        
        extracted = self._extractor.extract_document(
            document,
            progress_callback)
        
        return self._to_result(extracted)

    def _to_result(self, extracted: ExtractedDocument) \
        -> ExtractDocumentResult:
        
        return ExtractDocumentResult(extracted.document_id,
                                     extracted.filename,
                                     extracted.extracted_text,
                                     extracted.page_count)
