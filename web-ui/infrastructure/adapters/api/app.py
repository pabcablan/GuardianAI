from __future__ import annotations

from fastapi import FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware

from application.usecases.attach_document import AttachDocumentCommand
from application.usecases.create_chat import CreateChatCommand
from application.usecases.rename_chat import RenameChatCommand
from application.usecases.send_message import SendMessageCommand
from application.usecases.stream_response import StreamResponseCommand
from infrastructure.adapters.api.dependencies import build_container
from infrastructure.adapters.api.schemas import (
    AttachDocumentResponse,
    ChatDetailResponse,
    ChatMessageResponse,
    ChatSummaryResponse,
    CreateChatRequest,
    CreateChatResponse,
    RenameChatRequest,
    SendMessageRequest,
    SendMessageResponse,
    StreamResponse,
)


container = build_container()

app = FastAPI(
    title="GuardianAI Web UI Backend",
    version="0.1.0",
    description="API propia del modulo web-ui para gestionar el chat.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/chats", response_model=list[ChatSummaryResponse])
def list_chats() -> list[ChatSummaryResponse]:
    chats = container.list_chats.execute()
    return [
        ChatSummaryResponse(
            chat_id=chat.chat_id,
            title=chat.title,
            last_message_preview=chat.last_message_preview,
            updated_at=chat.updated_at,
        )
        for chat in chats
    ]


@app.post(
    "/api/chats",
    response_model=CreateChatResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_chat(payload: CreateChatRequest) -> CreateChatResponse:
    result = container.create_chat.execute(
        CreateChatCommand(title=payload.title)
    )
    return CreateChatResponse(chat_id=result.chat_id, title=result.title)


@app.get("/api/chats/{chat_id}", response_model=ChatDetailResponse)
def load_chat(chat_id: str) -> ChatDetailResponse:
    chat = container.load_chat.execute(chat_id)
    if chat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return ChatDetailResponse(
        chat_id=chat.chat_id,
        title=chat.title,
        messages=[
            ChatMessageResponse(
                message_id=message.message_id,
                role=message.role,
                content=message.content,
                created_at=message.created_at,
            )
            for message in chat.messages
        ],
    )


@app.post(
    "/api/chats/{chat_id}/messages",
    response_model=SendMessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def send_message(chat_id: str, payload: SendMessageRequest) -> SendMessageResponse:
    try:
        result = container.send_message.execute(
            SendMessageCommand(chat_id=chat_id, content=payload.content)
        )
    except KeyError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found.",
        ) from error

    return SendMessageResponse(
        user_message_id=result.user_message_id,
        assistant_message_id=result.assistant_message_id,
        assistant_content=result.assistant_content,
    )


@app.post(
    "/api/chats/{chat_id}/documents",
    response_model=AttachDocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def attach_document(
    chat_id: str,
    file: UploadFile = File(...),
) -> AttachDocumentResponse:
    try:
        result = container.attach_document.execute(
            AttachDocumentCommand(
                chat_id=chat_id,
                filename=file.filename or "document.pdf",
                content_type=file.content_type or "",
                content=await file.read(),
            )
        )
    except KeyError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found.",
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return AttachDocumentResponse(
        document_id=result.document_id,
        filename=result.filename,
    )


@app.patch("/api/chats/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
def rename_chat(chat_id: str, payload: RenameChatRequest) -> None:
    try:
        container.rename_chat.execute(
            RenameChatCommand(chat_id=chat_id, title=payload.title)
        )
    except KeyError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found.",
        ) from error


@app.delete("/api/chats/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chat(chat_id: str) -> None:
    container.delete_chat.execute(chat_id)


@app.get("/api/chats/{chat_id}/stream", response_model=StreamResponse)
def stream_response(chat_id: str) -> StreamResponse:
    try:
        chunks = container.stream_response.execute(
            StreamResponseCommand(chat_id=chat_id)
        )
    except KeyError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found.",
        ) from error

    return StreamResponse(chunks=chunks)
