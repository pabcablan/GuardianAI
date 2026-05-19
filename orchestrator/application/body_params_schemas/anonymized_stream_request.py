"""Schema for already anonymized stream requests."""

from pydantic import BaseModel, Field

from application.body_params_schemas.chat_history_message_request import (
    ChatHistoryMessageRequest,
)


class AnonymizedStreamRequest(BaseModel):
    """Represent a request that already contains anonymized text."""

    chat_id: str = Field(min_length=1)
    anonymized_text: str = Field(min_length=1)
    anonymization_id: str = Field(min_length=1)
    model: str = Field(min_length=1)
    history: list[ChatHistoryMessageRequest] = Field(default_factory=list)
    replacements: dict[str, str] = Field(default_factory=dict)
