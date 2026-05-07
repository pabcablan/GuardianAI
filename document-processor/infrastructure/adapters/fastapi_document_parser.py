import uuid

from fastapi import UploadFile, File

from infrastructure.ports.document_parser import DocumentParser
from domain.parsed_document import ParsedDocument

class FastAPIDocumentParser(DocumentParser):
    async def parse(self, uploaded_file: UploadFile = File(...)) -> ParsedDocument:
        return ParsedDocument(
            document_id=str(uuid.uuid4()),
            filename=uploaded_file.filename,
            content=await uploaded_file.read()
        )
