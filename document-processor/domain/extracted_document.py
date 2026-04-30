from dataclasses import dataclass

@dataclass(frozen=True)
class ExtractedDocument:
    document_id: str
    filename: str
    extracted_text: str
