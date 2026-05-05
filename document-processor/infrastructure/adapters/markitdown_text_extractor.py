from io import BytesIO

from markitdown import MarkItDown

from domain.parsed_document import ParsedDocument
from domain.extracted_document import ExtractedDocument
from infrastructure.ports.text_extractor import TextExtractor

class MarkitdownTextExtractor(TextExtractor):
    def __init__(self):
        self.mitd = MarkItDown()

    def extract_text(self, document: ParsedDocument) -> ExtractedDocument:
        content_bytesio = self.bytes_to_bytesio(document.content)
        mitd_result = self.mitd.convert(content_bytesio)
        mitd_text = mitd_result.text_content

        return ExtractedDocument(document_id=document.document_id,
                                 filename=document.filename,
                                 extracted_text=mitd_text)

    def bytes_to_bytesio(self, content: bytes) -> BytesIO:
        return BytesIO(content)
