"""Mappers from domain/use-case objects to API response schemas."""
from __future__ import annotations

from application.usecases.create_chat import CreateChatResult
from application.usecases.list_chats import ChatSummary
from domain.chat import Chat
from infrastructure.adapters.api.schemas import (
    ChatDetailResponse,
    ChatMessageResponse,
    ChatSummaryResponse,
    CreateChatResponse,
)


def to_create_chat_response(result: CreateChatResult) -> CreateChatResponse:
    """Map a chat creation result into an API response."""
    return CreateChatResponse(chat_id=result.chat_id, title=result.title)


def to_chat_summary_response(summary: ChatSummary) -> ChatSummaryResponse:
    """Map one chat summary into an API response."""
    return ChatSummaryResponse(
        chat_id=summary.chat_id,
        title=summary.title,
        last_message_preview=summary.last_message_preview,
        updated_at=summary.updated_at,
    )


def to_chat_detail_response(chat: Chat) -> ChatDetailResponse:
    """Map a complete chat into an API response."""
    return ChatDetailResponse(
        chat_id=chat.chat_id,
        title=chat.title,
        messages=[
            ChatMessageResponse(
                message_id=message.message_id,
                role=message.role,
                content=message.content,
                anonymized_content=message.anonymized_content,
                created_at=message.created_at,
            )
            for message in chat.messages
        ],
    )
