import pymupdf  
import pymupdf4llm

from infrastructure.ports.text_extractor import TextExtractor
from domain.parsed_document import ParsedDocument
from domain.extracted_document import ExtractedDocument

class PyMuPDFTextExtractor(TextExtractor):
    def extract_text(self, document: ParsedDocument) -> ExtractedDocument:
        pdf_content = pymupdf.open(stream=document.content, filetype="pdf")
        
        md = pymupdf4llm.to_markdown(pdf_content, ocr_language='spa')

        return ExtractedDocument(
            extracted_text=md,
            filename=document.filename,
            document_id=document.document_id
        )
    

