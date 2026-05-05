"""FastAPI document parser adapter."""
from __future__ import annotations

import uuid

from fastapi import File, UploadFile

from domain.parsed_document import ParsedDocument
from infrastructure.ports.document_parser import DocumentParser


class FastAPIDocumentParser(DocumentParser):
    """Parse FastAPI uploaded files into parsed documents."""

    async def parse(
        self,
        uploaded_file: UploadFile = File(...),
    ) -> ParsedDocument:
        """Parse an uploaded file.

        Args:
            uploaded_file (UploadFile): The uploaded document file.

        Returns:
            ParsedDocument: The parsed document metadata and content.
        """
        return ParsedDocument(
            document_id=str(uuid.uuid4()),
            filename=uploaded_file.filename,
            content=await uploaded_file.read(),
        )
