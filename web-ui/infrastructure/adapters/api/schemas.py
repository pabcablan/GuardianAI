from __future__ import annotations

from pydantic import BaseModel, Field


class CreateChatRequest(BaseModel):
    title: str | None = Field(default=None, max_length=120)


class CreateChatResponse(BaseModel):
    chat_id: str
    title: str


class ChatSummaryResponse(BaseModel):
    chat_id: str
    title: str
    last_message_preview: str
    updated_at: str


class ChatMessageResponse(BaseModel):
    message_id: str
    role: str
    content: str
    created_at: str


class ChatDetailResponse(BaseModel):
    chat_id: str
    title: str
    messages: list[ChatMessageResponse]


class SendMessageRequest(BaseModel):
    content: str = Field(min_length=1)


class SendMessageResponse(BaseModel):
    user_message_id: str
    assistant_message_id: str | None
    assistant_content: str | None


class RenameChatRequest(BaseModel):
    title: str = Field(min_length=1, max_length=120)


class AttachDocumentResponse(BaseModel):
    document_id: str
    filename: str


class AttachDocumentProgressResponse(BaseModel):
    event: str = "progress"
    stage: str
    current: int
    total: int
    message: str


class AttachDocumentCompletedResponse(BaseModel):
    event: str = "completed"
    document_id: str
    filename: str


class AttachDocumentErrorResponse(BaseModel):
    event: str = "error"
    detail: str


class StreamResponse(BaseModel):
    chunks: list[str]
