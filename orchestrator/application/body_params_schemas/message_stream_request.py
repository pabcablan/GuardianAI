"""Schema for message streaming requests."""

from pydantic import BaseModel, Field

from application.body_params_schemas.chat_history_message_request import (
    ChatHistoryMessageRequest,
)


class MessageStreamRequest(BaseModel):
    """Represent a prompt stream request from web-ui."""

    chat_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    model: str = Field(min_length=1)
    history: list[ChatHistoryMessageRequest] = Field(default_factory=list)
    settings: dict[str, str] = Field(default_factory=dict)
    replacements: dict[str, str] = Field(default_factory=dict)
