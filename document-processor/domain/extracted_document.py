from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class ExtractedDocument:
    document_id: str
    filename: str
    extracted_text: str
    page_count: int
    saved_path: Path | None = None
    extracted_text_path: Path | None = None
