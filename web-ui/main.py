"""FastAPI entrypoint and dependency composition for the web-ui module.

Run it from the `web-ui` directory with:
`uvicorn main:app --reload`
"""
from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass

from fastapi import FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from application.usecases.attach_document import (
    AttachDocumentCommand,
    AttachDocumentCompleted,
    AttachDocumentFailed,
    AttachDocumentProgress,
    AttachDocumentUseCase,
)
from application.usecases.create_chat import CreateChatCommand, CreateChatUseCase
from application.usecases.delete_chat import DeleteChatUseCase
from application.usecases.list_chats import ListChatsUseCase
from application.usecases.load_chat import LoadChatUseCase
from application.usecases.rename_chat import RenameChatCommand, RenameChatUseCase
from application.usecases.stream_message_response import (
    StreamMessageResponseCommand,
    StreamMessageResponseUseCase,
)
from application.usecases.stream_safe_response import (
    StreamSafeResponseCommand,
    StreamSafeResponseUseCase,
)
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
    SafeStreamChunkResponse,
    SafeStreamCompletedResponse,
    SafeStreamErrorResponse,
    StreamMessageRequest,
)
from infrastructure.adapters.connected_document_service import (
    ConnectedDocumentService,
)
from infrastructure.adapters.http_orchestrator_client import (
    HttpOrchestratorClient,
)
from infrastructure.adapters.http_orchestrator_document_client import (
    HttpOrchestratorDocumentClient,
)
from infrastructure.adapters.in_memory_chat_gateway import InMemoryChatGateway
from infrastructure.ports.external.orchestrator_response_port import (
    OrchestratorStreamChunk,
    OrchestratorStreamCompleted,
    OrchestratorStreamEvent,
    OrchestratorStreamFailed,
)


@dataclass(frozen=True)
class WebUiContainer:
    """Group the use cases exposed by the API.

    Attributes:
        create_chat (CreateChatUseCase): The create chat use case.
        list_chats (ListChatsUseCase): The list chats use case.
        load_chat (LoadChatUseCase): The load chat use case.
        attach_document (AttachDocumentUseCase): The attach document use case.
        delete_chat (DeleteChatUseCase): The delete chat use case.
        rename_chat (RenameChatUseCase): The rename chat use case.
        stream_safe_response (StreamSafeResponseUseCase): The document response
            stream use case through orchestrator.
        stream_message_response (StreamMessageResponseUseCase): The message
            response stream use case through orchestrator.
    """

    create_chat: CreateChatUseCase
    list_chats: ListChatsUseCase
    load_chat: LoadChatUseCase
    attach_document: AttachDocumentUseCase
    delete_chat: DeleteChatUseCase
    rename_chat: RenameChatUseCase
    stream_safe_response: StreamSafeResponseUseCase
    stream_message_response: StreamMessageResponseUseCase


def build_container() -> WebUiContainer:
    """Build the dependency graph for the web-ui backend.

    Returns:
        WebUiContainer: The configured use case container.
    """
    gateway = InMemoryChatGateway()
    document_processor = HttpOrchestratorDocumentClient()
    document_service = ConnectedDocumentService(gateway, document_processor)
    orchestrator = HttpOrchestratorClient()

    return WebUiContainer(
        create_chat=CreateChatUseCase(gateway),
        list_chats=ListChatsUseCase(gateway),
        load_chat=LoadChatUseCase(gateway),
        attach_document=AttachDocumentUseCase(document_service),
        delete_chat=DeleteChatUseCase(gateway),
        rename_chat=RenameChatUseCase(gateway),
        stream_safe_response=StreamSafeResponseUseCase(orchestrator),
        stream_message_response=StreamMessageResponseUseCase(orchestrator),
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


@app.post("/api/chats/{chat_id}/messages/stream")
def stream_message_response(
    chat_id: str,
    payload: StreamMessageRequest,
) -> StreamingResponse:
    """Stream a safe assistant response for a user message.

    Args:
        chat_id (str): The identifier of the target chat.
        payload (StreamMessageRequest): The message request body.

    Returns:
        StreamingResponse: The NDJSON safe response stream.
    """
    try:
        events = container.stream_message_response.execute(
            StreamMessageResponseCommand(
                chat_id=chat_id,
                content=payload.content,
            )
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return _build_safe_streaming_response(events)


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

    def event_stream() -> Iterator[str]:
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


@app.get("/api/chats/{chat_id}/documents/{document_id}/safe-stream")
def stream_safe_response(chat_id: str, document_id: str) -> StreamingResponse:
    """Stream safe response chunks for a processed document.

    Args:
        chat_id (str): The identifier of the target chat.
        document_id (str): The identifier of the processed document.

    Returns:
        StreamingResponse: The NDJSON safe response stream.
    """
    try:
        events = container.stream_safe_response.execute(
            StreamSafeResponseCommand(
                chat_id=chat_id,
                document_id=document_id,
            )
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return _build_safe_streaming_response(events)


def _build_safe_streaming_response(
    events: Iterator[OrchestratorStreamEvent],
) -> StreamingResponse:
    """Build an NDJSON response from orchestrator stream events.

    Args:
        events (Iterator[OrchestratorStreamEvent]): The stream events.

    Returns:
        StreamingResponse: The serialized safe stream.
    """
    def event_stream() -> Iterator[str]:
        """Serialize privacy-shield stream events as JSON lines.

        Yields:
            str: One JSON-encoded event followed by a newline.
        """
        try:
            for event in events:
                if isinstance(event, OrchestratorStreamChunk):
                    payload = SafeStreamChunkResponse(
                        content=event.content,
                    ).model_dump()
                elif isinstance(event, OrchestratorStreamCompleted):
                    payload = SafeStreamCompletedResponse().model_dump()
                elif isinstance(event, OrchestratorStreamFailed):
                    payload = SafeStreamErrorResponse(
                        detail=event.detail,
                    ).model_dump()
                else:
                    payload = SafeStreamErrorResponse(
                        detail="Unknown privacy-shield stream event.",
                    ).model_dump()

                yield json.dumps(payload, ensure_ascii=True) + "\n"
        except RuntimeError as error:
            payload = SafeStreamErrorResponse(detail=str(error)).model_dump()
            yield json.dumps(payload, ensure_ascii=True) + "\n"

    return StreamingResponse(
        event_stream(),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
