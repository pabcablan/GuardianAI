import uuid

from fastapi import UploadFile

from domain.parsed_document import ParsedDocument
from infrastructure.ports.document_parser import DocumentParser


class FastAPIDocumentParser(DocumentParser):
    """Adapt FastAPI uploads to the document parsing contract."""

    async def parse(self, uploaded_file: UploadFile) -> ParsedDocument:
        """Read an uploaded file and convert it into a parsed document.

        Args:
            uploaded_file (UploadFile): FastAPI upload received by the endpoint.

        Returns:
            ParsedDocument: Parsed document with metadata and raw content bytes.
        """
        return ParsedDocument(
            document_id=str(uuid.uuid4()),
            filename=uploaded_file.filename,
            content=await uploaded_file.read(),
        )
