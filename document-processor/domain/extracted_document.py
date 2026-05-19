from dataclasses import dataclass


@dataclass(frozen=True)
class ExtractedDocument:
    """Document metadata plus extracted text content."""

    document_id: str
    filename: str
    extracted_text: str
    extraction_method: str = "library"
