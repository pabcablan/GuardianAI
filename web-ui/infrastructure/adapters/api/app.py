"""FastAPI application that exposes the web-ui use cases."""
from __future__ import annotations

import json

from fastapi import FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from application.usecases.attach_document import AttachDocumentCommand
from application.usecases.attach_document import (
    AttachDocumentCompleted,
    AttachDocumentFailed,
    AttachDocumentProgress,
)
from application.usecases.create_chat import CreateChatCommand
from application.usecases.rename_chat import RenameChatCommand
from application.usecases.send_message import SendMessageCommand
from application.usecases.stream_response import StreamResponseCommand
from infrastructure.adapters.api.dependencies import build_container
from infrastructure.adapters.api.schemas import (
    AttachDocumentCompletedResponse,
    AttachDocumentErrorResponse,
    AttachDocumentProgressResponse,
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
    """Return the API health status.

    Returns:
        dict[str, str]: A simple status payload.
    """
    return {"status": "ok"}


@app.get("/api/chats", response_model=list[ChatSummaryResponse])
def list_chats() -> list[ChatSummaryResponse]:
    """List the chats available to the UI.

    Returns:
        list[ChatSummaryResponse]: The available chat summaries.
    """
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
    """Create a new chat.

    Args:
        payload (CreateChatRequest): The chat creation request body.

    Returns:
        CreateChatResponse: The created chat data.
    """
    result = container.create_chat.execute(
        CreateChatCommand(title=payload.title)
    )
    return CreateChatResponse(chat_id=result.chat_id, title=result.title)


@app.get("/api/chats/{chat_id}", response_model=ChatDetailResponse)
def load_chat(chat_id: str) -> ChatDetailResponse:
    """Load a complete chat conversation.

    Args:
        chat_id (str): The identifier of the chat to load.

    Returns:
        ChatDetailResponse: The chat detail and message history.

    Raises:
        HTTPException: If the chat does not exist.
    """
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
    """Send a user message and return the assistant response.

    Args:
        chat_id (str): The identifier of the target chat.
        payload (SendMessageRequest): The message request body.

    Returns:
        SendMessageResponse: The created message identifiers and response.

    Raises:
        HTTPException: If the target chat does not exist.
    """
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


@app.post("/api/chats/{chat_id}/documents/stream")
async def attach_document_stream(
    chat_id: str,
    file: UploadFile = File(...),
) -> StreamingResponse:
    """Attach a PDF to a chat and stream progress as NDJSON.

    Args:
        chat_id (str): The identifier of the target chat.
        file (UploadFile): The uploaded PDF file.

    Returns:
        StreamingResponse: The NDJSON event stream.

    Raises:
        HTTPException: If the chat is missing or the document is invalid.
    """
    filename = file.filename or "document.pdf"
    content_type = file.content_type or ""
    content = await file.read()

    try:
        events = container.attach_document.stream(
            AttachDocumentCommand(
                chat_id=chat_id,
                filename=filename,
                content_type=content_type,
                content=content,
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

    def event_stream():
        """Serialize attachment events as JSON lines.

        Yields:
            str: One JSON-encoded event followed by a newline.
        """
        try:
            for event in events:
                if isinstance(event, AttachDocumentProgress):
                    payload = AttachDocumentProgressResponse(
                        stage=event.stage,
                        current=event.current,
                        total=event.total,
                        message=event.message,
                    ).model_dump()
                elif isinstance(event, AttachDocumentCompleted):
                    payload = AttachDocumentCompletedResponse(
                        document_id=event.document_id,
                        filename=event.filename,
                    ).model_dump()
                elif isinstance(event, AttachDocumentFailed):
                    payload = AttachDocumentErrorResponse(
                        detail=event.detail,
                    ).model_dump()
                else:
                    payload = AttachDocumentErrorResponse(
                        detail="Unknown attach document event.",
                    ).model_dump()

                yield json.dumps(payload, ensure_ascii=True) + "\n"
        except RuntimeError as error:
            payload = AttachDocumentErrorResponse(detail=str(error)).model_dump()
            yield json.dumps(payload, ensure_ascii=True) + "\n"

    return StreamingResponse(
        event_stream(),
        media_type="application/x-ndjson",
    )


@app.patch("/api/chats/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
def rename_chat(chat_id: str, payload: RenameChatRequest) -> None:
    """Rename an existing chat.

    Args:
        chat_id (str): The identifier of the chat to rename.
        payload (RenameChatRequest): The rename request body.

    Raises:
        HTTPException: If the target chat does not exist.
    """
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
    """Delete a chat by identifier.

    Args:
        chat_id (str): The identifier of the chat to delete.
    """
    container.delete_chat.execute(chat_id)


@app.get("/api/chats/{chat_id}/stream", response_model=StreamResponse)
def stream_response(chat_id: str) -> StreamResponse:
    """Return chunks from the latest assistant response.

    Args:
        chat_id (str): The identifier of the chat.

    Returns:
        StreamResponse: The response chunks.

    Raises:
        HTTPException: If the target chat does not exist.
    """
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
