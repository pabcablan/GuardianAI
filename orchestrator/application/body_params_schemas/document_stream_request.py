"""Schema for safe document stream requests."""

from pydantic import BaseModel, Field


class DocumentStreamRequest(BaseModel):
    """Represent a document safe-stream request from web-ui."""

    chat_id: str = Field(min_length=1)
    document_id: str = Field(min_length=1)
    model: str = Field(min_length=1)
    settings: dict[str, str] = Field(default_factory=dict)
    replacements: dict[str, str] = Field(default_factory=dict)
