"""Schema for one anonymized chat history message."""

from pydantic import BaseModel, Field


class ChatHistoryMessageRequest(BaseModel):
    """Represent one anonymized history message from web-ui."""

    role: str = Field(min_length=1)
    content: str = Field(min_length=1)
