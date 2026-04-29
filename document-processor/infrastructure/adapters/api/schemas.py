from __future__ import annotations

from pydantic import BaseModel


class ExtractionProgressResponse(BaseModel):
    event: str = "progress"
    stage: str
    current: int
    total: int
    message: str


class ExtractionCompletedResponse(BaseModel):
    event: str = "completed"
    document_id: str
    filename: str
    extracted_text: str
    page_count: int


class ExtractionErrorResponse(BaseModel):
    event: str = "error"
    detail: str
