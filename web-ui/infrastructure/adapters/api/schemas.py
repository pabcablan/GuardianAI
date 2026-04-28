"""Pydantic schemas used by the web-ui HTTP endpoints."""
from __future__ import annotations

from pydantic import BaseModel, Field


class CreateChatRequest(BaseModel):
    """Represent the request body used to create a chat.

    Attributes:
        title (str | None): The optional chat title.
    """

    title: str | None = Field(default=None, max_length=120)


class CreateChatResponse(BaseModel):
    """Represent the response returned after creating a chat.

    Attributes:
        chat_id (str): The created chat identifier.
        title (str): The created chat title.
    """

    chat_id: str
    title: str


class ChatSummaryResponse(BaseModel):
    """Represent a chat summary returned by the API.

    Attributes:
        chat_id (str): The chat identifier.
        title (str): The chat title.
        last_message_preview (str): The latest message preview.
        updated_at (str): The displayed update timestamp.
    """

    chat_id: str
    title: str
    last_message_preview: str
    updated_at: str


class ChatMessageResponse(BaseModel):
    """Represent a chat message returned by the API.

    Attributes:
        message_id (str): The message identifier.
        role (str): The sender role.
        content (str): The message content.
        created_at (str): The message timestamp.
    """

    message_id: str
    role: str
    content: str
    created_at: str


class ChatDetailResponse(BaseModel):
    """Represent a complete chat and its message history.

    Attributes:
        chat_id (str): The chat identifier.
        title (str): The chat title.
        messages (list[ChatMessageResponse]): The chat message history.
    """

    chat_id: str
    title: str
    messages: list[ChatMessageResponse]


class SendMessageRequest(BaseModel):
    """Represent the request body used to send a message.

    Attributes:
        content (str): The user message content.
    """

    content: str = Field(min_length=1)


class SendMessageResponse(BaseModel):
    """Represent the response returned after sending a message.

    Attributes:
        user_message_id (str): The user message identifier.
        assistant_message_id (str | None): The assistant message identifier.
        assistant_content (str | None): The assistant response content.
    """

    user_message_id: str
    assistant_message_id: str | None
    assistant_content: str | None


class RenameChatRequest(BaseModel):
    """Represent the request body used to rename a chat.

    Attributes:
        title (str): The requested new chat title.
    """

    title: str = Field(min_length=1, max_length=120)


class AttachDocumentProgressResponse(BaseModel):
    """Represent a document attachment progress response.

    Attributes:
        event (str): The event type.
        stage (str): The current processing stage.
        current (int): The current progress value.
        total (int): The total progress value.
        message (str): A human-readable progress message.
    """

    event: str = "progress"
    stage: str
    current: int
    total: int
    message: str


class AttachDocumentCompletedResponse(BaseModel):
    """Represent a successful document attachment response.

    Attributes:
        event (str): The event type.
        document_id (str): The processed document identifier.
        filename (str): The processed document filename.
    """

    event: str = "completed"
    document_id: str
    filename: str


class AttachDocumentErrorResponse(BaseModel):
    """Represent a failed document attachment response.

    Attributes:
        event (str): The event type.
        detail (str): The error detail.
    """

    event: str = "error"
    detail: str


class StreamResponse(BaseModel):
    """Represent response chunks used to simulate streaming.

    Attributes:
        chunks (list[str]): The response chunks.
    """

    chunks: list[str]
