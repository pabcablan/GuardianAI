from dataclasses import dataclass

@dataclass(frozen=True)
class ProcessingDocument:
    filename: str
    content: bytes

    def __post_init__(self) -> None:
        if not self.filename.strip():
            raise ValueError("Filename cannot be empty.")
        if not self.content:
            raise ValueError("Document content cannot be empty.")
        
    #TODO move checking of content type to the API layer