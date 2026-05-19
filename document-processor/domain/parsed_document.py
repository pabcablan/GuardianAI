from dataclasses import dataclass


@dataclass(frozen=True)
class ParsedDocument:
    """Parsed document metadata and raw binary content."""

    document_id: str
    filename: str
    content: bytes

    def __post_init__(self) -> None:
        """Validate required parsed document fields."""
        if not self.filename.strip():
            raise ValueError("Filename cannot be empty.")
        if not self.content:
            raise ValueError("Document content cannot be empty.")
