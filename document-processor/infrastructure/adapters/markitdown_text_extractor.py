from markitdown import Markitdown

from domain.parsed_document import ParsedDocument
from domain.extracted_document import ExtractedDocument
from ports.text_extractor import TextExtractor

class MarkitdownTextExtractor(TextExtractor):
    def __init__(self):
        self.mitd = Markitdown()

    def extract_text(self, document: ParsedDocument) -> ExtractedDocument:
        extracted_text = self.mitd.convert(document.content)
        return ExtractedDocument(extracted_text=extracted_text)