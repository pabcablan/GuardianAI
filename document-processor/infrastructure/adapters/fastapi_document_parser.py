import uuid

from fastapi import UploadFile, File

from ports.document_parser import DocumentParser
from domain.parsed_document import ParsedDocument

class FastAPIDocumentParser(DocumentParser):
    def parse(self, file: UploadFile = File(...)) -> ParsedDocument:
        return ParsedDocument(
            document_id=str(uuid.uuid4()),
            filename=file.filename,
            content=file.file.read()
        )