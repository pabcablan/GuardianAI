"""PyMuPDF text extractor adapter."""
from __future__ import annotations

from fastapi.concurrency import run_in_threadpool
import pymupdf
import pymupdf4llm

from domain.extracted_document import ExtractedDocument
from domain.parsed_document import ParsedDocument
from infrastructure.ports.text_extractor import TextExtractor


class PyMuPDFTextExtractor(TextExtractor):
    """Extract text from PDF documents using PyMuPDF."""

    async def extract_text(self, document: ParsedDocument) -> ExtractedDocument:
        """Extract text from a parsed PDF document.

        Args:
            document (ParsedDocument): The parsed PDF document.

        Returns:
            ExtractedDocument: The document with extracted text.
        """
        return await run_in_threadpool(self._extract_text_sync, document)

    def _extract_text_sync(self, document: ParsedDocument) -> ExtractedDocument:
        """Run the blocking PyMuPDF extraction.

        Args:
            document (ParsedDocument): The parsed PDF document.

        Returns:
            ExtractedDocument: The document with extracted text.
        """
        pdf_content = pymupdf.open(stream=document.content, filetype="pdf")
        try:
            extracted_text = pymupdf4llm.to_markdown(
                pdf_content,
                ocr_language="spa",
            )
        finally:
            pdf_content.close()

        return ExtractedDocument(
            extracted_text=extracted_text,
            filename=document.filename,
            document_id=document.document_id,
        )
