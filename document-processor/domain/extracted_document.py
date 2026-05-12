"""
Represents a document that has been processed and had its text extracted.
    
Attributes:
    document_id: A unique identifier for the document.
    filename: The name of the original document file.
    extracted_text: The text that was extracted from the document.
"""

from dataclasses import dataclass

@dataclass(frozen=True)
class ExtractedDocument:
    document_id: str
    filename: str
    extracted_text: str
    extraction_method: str = "library"
