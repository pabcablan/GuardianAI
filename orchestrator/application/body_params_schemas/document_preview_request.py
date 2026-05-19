"""Schema for document anonymization preview requests."""

from pydantic import BaseModel, Field


class DocumentPreviewRequest(BaseModel):
    """Represent a document anonymization preview request."""

    chat_id: str = Field(min_length=1)
    document_id: str = Field(min_length=1)
    settings: dict[str, str] = Field(default_factory=dict)
