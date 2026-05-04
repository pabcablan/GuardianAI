"""
Represents a parsed document with its metadata and content.
    
Attributes:
    document_id: A unique identifier for the document.
    filename: The name of the document file.
    content: The raw content of the document in bytes.
"""

from dataclasses import dataclass

@dataclass(frozen=True)
class ParsedDocument:
    document_id: str
    filename: str
    content: bytes

    def __post_init__(self) -> None:
        if not self.filename.strip():
            raise ValueError("Filename cannot be empty.")
        if not self.content:
            raise ValueError("Document content cannot be empty.")