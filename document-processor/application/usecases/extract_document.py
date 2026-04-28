from dataclasses import dataclass

from domain.extracted_document import ExtractedDocument
from domain.extraction_progress import ExtractionProgressCallback
from domain.processing_document import ProcessingDocument
from infrastructure.ports.document_extractor import DocumentExtractor


@dataclass(frozen=True)
class ExtractDocumentCommand: #TODO copy of processing_document?
    filename: str
    content_type: str #TODO should this be here? or in the API layer?
    content: bytes


@dataclass(frozen=True)
class ExtractDocumentResult: #TODO copy of extracted_document?
    document_id: str
    filename: str
    extracted_text: str
    page_count: int


class ExtractDocumentUseCase:
    def __init__(self, extractor: DocumentExtractor) -> None:
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
                                     extracted.num_pages)
