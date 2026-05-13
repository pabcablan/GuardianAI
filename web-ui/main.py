from __future__ import annotations

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from application.services.anonymized_history import AnonymizedHistoryBuilder
from application.services.model_readiness import ModelReadinessService
from application.services.processed_document_registry import (
    ProcessedDocumentRegistry,
)
from application.usecases.attach_document import AttachDocumentCommand
from application.usecases.create_chat import CreateChatCommand
from application.usecases.rename_chat import RenameChatCommand
from application.usecases.stream_message_response import (
    StreamMessageResponseCommand,
)
from application.usecases.stream_safe_response import (
    StreamSafeResponseCommand,
)
from config import (
    DOCUMENT_MODEL_NAME,
    MODEL_PROVIDER_BASE_URL,
    MODEL_STATUS_TIMEOUT_SECONDS,
    PRIVACY_MODEL_NAME,
)
from infrastructure.adapters.api.context import (
    make_assistant_message,
    make_message,
)
from infrastructure.adapters.api.mappers import (
    to_chat_detail_response,
    to_chat_summary_response,
    to_create_chat_response,
)
from infrastructure.adapters.api.schemas import (
    AnonymizedPreviewResponse,
    ChatDetailResponse,
    ChatSummaryResponse,
    ContinueAnonymizedRequest,
    CreateChatRequest,
    CreateChatResponse,
    DocumentAnonymizationRequest,
    DocumentSafeStreamRequest,
    RenameChatRequest,
    StreamMessageRequest,
)
from infrastructure.adapters.api.streaming import (
    build_document_streaming_response,
    build_safe_streaming_response,
)
from infrastructure.adapters.orchestrator.base import OrchestratorClientError
from infrastructure.dependency_container import build_container
from infrastructure.ports.external.orchestrator_response_port import (
    OrchestratorAnonymizationPreviewRequest,
    OrchestratorAnonymizedResponseRequest,
    OrchestratorDocumentAnonymizationPreviewRequest,
)


container = build_container()
processed_document_registry = ProcessedDocumentRegistry()
anonymized_history_builder = AnonymizedHistoryBuilder(
    container.chat_repository,
)
model_readiness_service = ModelReadinessService(
    base_url=MODEL_PROVIDER_BASE_URL,
    privacy_model_name=PRIVACY_MODEL_NAME,
    document_model_name=DOCUMENT_MODEL_NAME,
    timeout_seconds=MODEL_STATUS_TIMEOUT_SECONDS,
)

app = FastAPI(
    title="GuardianAI Web UI Backend",
    version="0.1.0",
    description="API propia del módulo web-ui para gestionar el chat.",
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
    """Return the API health status."""
    return {"status": "ok"}


@app.get("/api/system/model-readiness")
def model_readiness() -> dict[str, object]:
    """Return whether the required backend models are loaded."""
    return model_readiness_service.get_readiness()


@app.get("/api/chats", response_model=list[ChatSummaryResponse])
def list_chats() -> list[ChatSummaryResponse]:
    """List the chats available to the UI."""
    chats = container.list_chats.execute()
    return [to_chat_summary_response(chat) for chat in chats]


@app.post(
    "/api/chats",
    response_model=CreateChatResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_chat(payload: CreateChatRequest) -> CreateChatResponse:
    """Create a new chat."""
    result = container.create_chat.execute(
        CreateChatCommand(title=payload.title),
    )
    return to_create_chat_response(result)


@app.get("/api/chats/{chat_id}", response_model=ChatDetailResponse)
def load_chat(chat_id: str) -> ChatDetailResponse:
    """Load a complete chat conversation."""
    chat = container.load_chat.execute(chat_id)
    if chat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return to_chat_detail_response(chat)


@app.post("/api/chats/{chat_id}/messages/stream")
def stream_message_response(
    chat_id: str,
    payload: StreamMessageRequest,
):
    """Stream a safe assistant response for a user message."""
    content = payload.content.strip()
    user_message = make_message(role="user", content=content)

    try:
        history = anonymized_history_builder.build(chat_id)
        container.chat_repository.append_message(chat_id, user_message)
        events = container.stream_message_response.execute(
            StreamMessageResponseCommand(
                chat_id=chat_id,
                content=content,
                model=payload.model,
                history=history,
                settings=payload.settings,
            ),
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except KeyError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat no encontrado.",
        ) from error

    return build_safe_streaming_response(
        events,
        chat_repository=container.chat_repository,
        make_assistant_message=make_assistant_message,
        chat_id=chat_id,
        user_message_id=user_message.message_id,
    )


@app.post(
    "/api/chats/{chat_id}/messages/anonymize-preview",
    response_model=AnonymizedPreviewResponse,
)
def preview_message_anonymization(
    chat_id: str,
    payload: StreamMessageRequest,
) -> AnonymizedPreviewResponse:
    """Anonymize a user message before assistant processing."""
    content = payload.content.strip()
    user_message = make_message(role="user", content=content)

    try:
        container.chat_repository.append_message(chat_id, user_message)
        preview = container.orchestrator_response.preview_message_anonymization(
            OrchestratorAnonymizationPreviewRequest(
                chat_id=chat_id,
                content=content,
                model=payload.model,
                settings=payload.settings,
            ),
        )
        container.chat_repository.update_message_anonymized_content(
            user_message.message_id,
            preview.anonymized_content,
        )
    except KeyError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat no encontrado.",
        ) from error

    return AnonymizedPreviewResponse(
        message_id=user_message.message_id,
        anonymized_content=preview.anonymized_content,
        anonymization_id=preview.anonymization_id,
        replacement_count=preview.replacement_count,
        extraction_method=preview.extraction_method,
    )


@app.post("/api/chats/{chat_id}/anonymized/stream")
def stream_approved_anonymized_response(
    chat_id: str,
    payload: ContinueAnonymizedRequest,
):
    """Stream a response after the user approves anonymized text."""
    events = container.orchestrator_response.stream_anonymized_response(
        OrchestratorAnonymizedResponseRequest(
            chat_id=chat_id,
            anonymized_content=payload.anonymized_content,
            anonymization_id=payload.anonymization_id,
            model=payload.model,
            history=anonymized_history_builder.build(
                chat_id,
                exclude_last_content=payload.anonymized_content,
            ),
        ),
    )
    return build_safe_streaming_response(
        events,
        chat_repository=container.chat_repository,
        make_assistant_message=make_assistant_message,
        chat_id=chat_id,
    )


@app.post("/api/chats/{chat_id}/documents/stream")
async def attach_document_stream(
    chat_id: str,
    file: UploadFile = File(...),
    prompt: str = Form(""),
):
    """Attach a PDF to a chat and stream progress as NDJSON."""
    filename = file.filename or "document.pdf"
    content_type = file.content_type or ""
    content = await file.read()

    user_message = make_message(
        role="user",
        content=prompt.strip() or f"Documento: {filename}",
    )
    try:
        container.chat_repository.append_message(chat_id, user_message)
        events = container.attach_document.stream(
            AttachDocumentCommand(
                chat_id=chat_id,
                filename=filename,
                content_type=content_type,
                content=content,
                prompt=prompt,
            ),
        )
    except KeyError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat no encontrado.",
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    def remember_user_message(document_id: str) -> None:
        processed_document_registry.remember_user_message(
            document_id=document_id,
            user_message_id=user_message.message_id,
        )

    return build_document_streaming_response(
        events,
        remember_user_message=remember_user_message,
    )


@app.patch("/api/chats/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
def rename_chat(chat_id: str, payload: RenameChatRequest) -> None:
    """Rename an existing chat."""
    try:
        container.rename_chat.execute(
            RenameChatCommand(chat_id=chat_id, title=payload.title),
        )
    except KeyError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat no encontrado.",
        ) from error


@app.delete("/api/chats/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chat(chat_id: str) -> None:
    """Delete a chat by identifier."""
    container.delete_chat.execute(chat_id)


@app.post("/api/chats/{chat_id}/documents/{document_id}/safe-stream")
def stream_safe_response(
    chat_id: str,
    document_id: str,
    payload: DocumentSafeStreamRequest,
):
    """Stream safe response chunks for a processed document."""
    try:
        events = container.stream_safe_response.execute(
            StreamSafeResponseCommand(
                chat_id=chat_id,
                document_id=document_id,
                model=payload.model,
                settings=payload.settings,
            ),
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return build_safe_streaming_response(
        events,
        chat_repository=container.chat_repository,
        make_assistant_message=make_assistant_message,
        chat_id=chat_id,
        user_message_id=processed_document_registry.get_user_message_id(
            document_id,
        ),
    )


@app.post(
    "/api/chats/{chat_id}/documents/{document_id}/anonymize-preview",
    response_model=AnonymizedPreviewResponse,
)
def preview_document_anonymization(
    chat_id: str,
    document_id: str,
    payload: DocumentAnonymizationRequest,
) -> AnonymizedPreviewResponse:
    """Anonymize a processed document before assistant processing."""
    user_message_id = processed_document_registry.get_user_message_id(
        document_id,
    )
    if user_message_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Processed document message not found.",
        )

    preview = container.orchestrator_response.preview_document_anonymization(
        OrchestratorDocumentAnonymizationPreviewRequest(
            chat_id=chat_id,
            document_id=document_id,
            settings=payload.settings,
        ),
    )
    container.chat_repository.update_message_anonymized_content(
        user_message_id,
        preview.anonymized_content,
    )

    return AnonymizedPreviewResponse(
        message_id=user_message_id,
        anonymized_content=preview.anonymized_content,
        anonymization_id=preview.anonymization_id,
        replacement_count=preview.replacement_count,
        extraction_method=preview.extraction_method,
    )


@app.get(
    "/api/chats/{chat_id}/documents/{document_id}/anonymized-pdf-preview",
)
def download_anonymized_pdf_preview(
    chat_id: str,
    document_id: str,
    anonymization_id: str,
) -> Response:
    """Return a visual anonymized PDF preview for a processed document."""
    if processed_document_registry.get_user_message_id(document_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Processed document message not found.",
        )

    try:
        preview = container.orchestrator_response.get_anonymized_pdf_preview(
            document_id=document_id,
            anonymization_id=anonymization_id,
        )
    except OrchestratorClientError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error

    return Response(
        content=preview.content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{preview.filename}"',
        },
    )
