from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class ExtractedDocument:
    document_id: str
    filename: str
    extracted_text: str
    num_pages: int
    _saved_path: Path | None = None
    _extracted_text_path: Path | None = None
