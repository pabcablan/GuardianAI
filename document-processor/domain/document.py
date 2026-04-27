from __future__ import annotations #TODO remove 

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path


PDF_CONTENT_TYPE = "application/pdf"

#TODO: consider moving each dataclass to its own file

@dataclass(frozen=True)
class ProcessingDocument:
    filename: str
    content_type: str
    content: bytes

    def __post_init__(self) -> None:
        if not self.filename.strip():
            raise ValueError("Filename cannot be empty.")
        if not self.content:
            raise ValueError("Document content cannot be empty.")
        if not self.is_pdf():
            raise ValueError("Only PDF documents are supported.")

    def is_pdf(self) -> bool:
        return (self.content_type == PDF_CONTENT_TYPE 
                or self.filename.lower().endswith(".pdf"))


@dataclass(frozen=True)
class ExtractionProgress:
    stage: str
    current: int
    total: int
    message: str


ExtractionProgressCallback = Callable[[ExtractionProgress], None]


@dataclass(frozen=True)
class ExtractedDocument:
    document_id: str
    filename: str
    extracted_text: str
    page_count: int
    saved_path: Path | None = None
    extracted_text_path: Path | None = None
