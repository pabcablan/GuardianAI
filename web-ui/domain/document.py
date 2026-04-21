from __future__ import annotations

from dataclasses import dataclass


PDF_CONTENT_TYPE = "application/pdf"


@dataclass(frozen=True)
class DocumentAttachment:
    filename: str
    content_type: str
    content: bytes

    def __post_init__(self) -> None:
        if not self.filename.strip():
            raise ValueError("Filename cannot be empty.")
        if not self.is_pdf():
            raise ValueError("Only PDF documents are supported.")

    def is_pdf(self) -> bool:
        return (
            self.content_type == PDF_CONTENT_TYPE
            or self.filename.lower().endswith(".pdf")
        )
