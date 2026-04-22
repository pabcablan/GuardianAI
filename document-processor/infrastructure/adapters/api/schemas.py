from __future__ import annotations

from pydantic import BaseModel


class ExtractDocumentResponse(BaseModel):
    document_id: str
    filename: str
    extracted_text: str
    page_count: int
