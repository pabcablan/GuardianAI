from pathlib import Path
from uuid import uuid4

from domain.extracted_document import ExtractedDocument
from domain.extraction_progress import ExtractionProgressCallback
from domain.processing_document import ProcessingDocument
from infrastructure.adapters.extract_vlm import save_extracted_text, save_uploaded_pdf
from infrastructure.adapters.pdf_text_extractor import extract_pdf_text_with_fallback
from infrastructure.ports.document_extractor_port import DocumentExtractorPort


class LocalDocumentExtractor(DocumentExtractorPort):
    def __init__(self, storage_dir: Path) -> None:
        self._storage_dir = storage_dir
        self._storage_dir.mkdir(parents=True, exist_ok=True)

    def extract_document(self, document: ProcessingDocument,
        progress_callback: ExtractionProgressCallback | None = None) -> ExtractedDocument:
        
        document_id = f"doc-{uuid4().hex}"
        safe_filename = Path(document.filename).name
        pdf_path = save_uploaded_pdf(
            document.content,
            self._storage_dir / f"{document_id}_{safe_filename}",
        )

        extracted_text, page_count = extract_pdf_text_with_fallback(
            document.content,
            progress_callback=progress_callback,
        )
        text_path = save_extracted_text(
            extracted_text,
            pdf_path.with_suffix(".txt"),
        )

        return ExtractedDocument(
            document_id=document_id,
            filename=safe_filename,
            extracted_text=extracted_text,
            page_count=page_count,
            saved_path=pdf_path,
            extracted_text_path=text_path,
        )
