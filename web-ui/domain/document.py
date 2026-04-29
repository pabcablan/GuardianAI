"""Domain model for documents accepted by the web chat."""
from __future__ import annotations

from dataclasses import dataclass


PDF_CONTENT_TYPE = "application/pdf"


@dataclass(frozen=True)
class DocumentAttachment:
    """Represent a document uploaded by the user.

    Attributes:
        filename (str): The uploaded document filename.
        content_type (str): The uploaded document MIME type.
        content (bytes): The uploaded document bytes.
    """

    filename: str
    content_type: str
    content: bytes

    def __post_init__(self) -> None:
        """Validate the uploaded document.

        Raises:
            ValueError: If the filename is empty or the document is not a PDF.
        """
        if not self.filename.strip():
            raise ValueError("Filename cannot be empty.")
        if not self.is_pdf():
            raise ValueError("Only PDF documents are supported.")

    def is_pdf(self) -> bool:
        """Return whether the upload is identified as a PDF.

        Returns:
            bool: True if the upload has a PDF MIME type or extension, False
            otherwise.
        """
        return (
            self.content_type == PDF_CONTENT_TYPE
            or self.filename.lower().endswith(".pdf")
        )
