"""Domain data for processed documents stored by orchestrator."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProcessedDocumentContext:
    """Store extracted document text and the optional user prompt.

    Attributes:
        extracted_text (str): The text returned by document-processor.
        prompt (str): The optional prompt sent with the uploaded document.
        filename (str): The original uploaded filename.
        content_type (str): The original uploaded content type.
        content (bytes): The original uploaded document bytes.
    """

    extracted_text: str
    prompt: str = ""
    filename: str = "document.pdf"
    content_type: str = "application/pdf"
    content: bytes = b""
