"""FastAPI entrypoint and routes for the web-ui module.

Run it from the `web-ui` directory with:
`uvicorn main:app --reload`
"""
from __future__ import annotations

import os

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from application.usecases.attach_document import AttachDocumentCommand
from application.usecases.create_chat import CreateChatCommand
from application.usecases.rename_chat import RenameChatCommand
from application.usecases.stream_message_response import (
    StreamMessageResponseCommand,
)
from application.usecases.stream_safe_response import (
    StreamSafeResponseCommand,
)
from infrastructure.adapters.api.context import (
    WebUiApiState,
    make_assistant_message,
    make_message,
)
from infrastructure.adapters.api.schemas import (
    AnonymizedPreviewResponse,
    ChatDetailResponse,
    ChatMessageResponse,
    ChatSummaryResponse,
    ContinueAnonymizedRequest,
    CreateChatRequest,
    CreateChatResponse,
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
    OrchestratorChatHistoryMessage,
    OrchestratorDocumentAnonymizationPreviewRequest,
)

load_dotenv()

MODEL_PROVIDER_BASE_URL = os.getenv(
    "MODEL_PROVIDER_BASE_URL",
    "http://127.0.0.1:8006",
)
PRIVACY_MODEL_NAME = os.getenv("PRIVACY_MODEL_NAME", "privacy_anonymizer")
DOCUMENT_MODEL_NAME = os.getenv("DOCUMENT_MODEL_NAME", "document_extractor")
MODEL_STATUS_TIMEOUT_SECONDS = 2.0


container = build_container()
api_state = WebUiApiState()

app = FastAPI(
    title="GuardianAI Web UI Backend",
    version="0.1.0",
    description="API propia del m?dulo web-ui para gestionar el chat.",
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


@app.get("/api/system/model-readiness")
def model_readiness() -> dict[str, object]:
    """Return whether the required backend models are loaded.

    Returns:
        dict[str, object]: The model readiness state consumed by the UI.
    """
    return _get_model_readiness()


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
        CreateChatCommand(title=payload.title),
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
                anonymized_content=message.anonymized_content,
                created_at=message.created_at,
            )
            for message in chat.messages
        ],
    )


@app.post("/api/chats/{chat_id}/messages/stream")
def stream_message_response(
    chat_id: str,
    payload: StreamMessageRequest,
):
    """Stream a safe assistant response for a user message.

    Args:
        chat_id (str): The identifier of the target chat.
        payload (StreamMessageRequest): The message request body.

    Returns:
        StreamingResponse: The NDJSON safe response stream.
    """
    content = payload.content.strip()
    model = payload.model
    history = _build_anonymized_history(chat_id)
    user_message = make_message(role="user", content=content)

    try:
        container.chat_repository.append_message(chat_id, user_message)
        events = container.stream_message_response.execute(
            StreamMessageResponseCommand(
                chat_id=chat_id,
                content=content,
                model=model,
                history=history,
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
    """Anonymize a user message before assistant processing.

    Args:
        chat_id (str): The identifier of the target chat.
        payload (StreamMessageRequest): The message request body.

    Returns:
        AnonymizedPreviewResponse: The anonymized text preview.
    """
    content = payload.content.strip()
    user_message = make_message(role="user", content=content)

    try:
        container.chat_repository.append_message(chat_id, user_message)
        preview = container.orchestrator_response.preview_message_anonymization(
            OrchestratorAnonymizationPreviewRequest(
                chat_id=chat_id,
                content=content,
                model=payload.model,
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
    )


@app.post("/api/chats/{chat_id}/anonymized/stream")
def stream_approved_anonymized_response(
    chat_id: str,
    payload: ContinueAnonymizedRequest,
):
    """Stream a response after the user approves anonymized text.

    Args:
        chat_id (str): The identifier of the target chat.
        payload (ContinueAnonymizedRequest): The approved anonymized text.

    Returns:
        StreamingResponse: The NDJSON safe response stream.
    """
    events = container.orchestrator_response.stream_anonymized_response(
        OrchestratorAnonymizedResponseRequest(
            chat_id=chat_id,
            anonymized_content=payload.anonymized_content,
            anonymization_id=payload.anonymization_id,
            model=payload.model,
            history=_build_anonymized_history(
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
    """Attach a PDF to a chat and stream progress as NDJSON.

    Args:
        chat_id (str): The identifier of the target chat.
        file (UploadFile): The uploaded PDF file.
        prompt (str): The optional prompt to combine with the document text.

    Returns:
        StreamingResponse: The NDJSON event stream.
    """
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
        """Store the user message linked to a processed document.

        Args:
            document_id (str): The processed document identifier.
        """
        api_state.processed_document_user_messages[document_id] = (
            user_message.message_id
        )

    return build_document_streaming_response(
        events,
        remember_user_message=remember_user_message,
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
            RenameChatCommand(chat_id=chat_id, title=payload.title),
        )
    except KeyError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat no encontrado.",
        ) from error


@app.delete("/api/chats/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chat(chat_id: str) -> None:
    """Delete a chat by identifier.

    Args:
        chat_id (str): The identifier of the chat to delete.
    """
    container.delete_chat.execute(chat_id)


@app.get("/api/chats/{chat_id}/documents/{document_id}/safe-stream")
def stream_safe_response(chat_id: str, document_id: str, model: str):
    """Stream safe response chunks for a processed document.

    Args:
        chat_id (str): The identifier of the target chat.
        document_id (str): The identifier of the processed document.
        model (str): The AI model selected by the user.

    Returns:
        StreamingResponse: The NDJSON safe response stream.
    """
    try:
        events = container.stream_safe_response.execute(
            StreamSafeResponseCommand(
                chat_id=chat_id,
                document_id=document_id,
                model=model,
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
        user_message_id=api_state.processed_document_user_messages.get(
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
) -> AnonymizedPreviewResponse:
    """Anonymize a processed document before assistant processing.

    Args:
        chat_id (str): The identifier of the target chat.
        document_id (str): The processed document identifier.

    Returns:
        AnonymizedPreviewResponse: The anonymized document preview.
    """
    user_message_id = api_state.processed_document_user_messages.get(
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
    )


@app.get(
    "/api/chats/{chat_id}/documents/{document_id}/anonymized-pdf-preview",
)
def download_anonymized_pdf_preview(
    chat_id: str,
    document_id: str,
    anonymization_id: str,
) -> Response:
    """Return a visual anonymized PDF preview for a processed document.

    Args:
        chat_id (str): The identifier of the target chat.
        document_id (str): The processed document identifier.
        anonymization_id (str): The anonymization session identifier.

    Returns:
        Response: The anonymized PDF preview bytes.
    """
    if api_state.processed_document_user_messages.get(document_id) is None:
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


def _build_anonymized_history(
    chat_id: str,
    exclude_last_content: str | None = None,
) -> list[OrchestratorChatHistoryMessage]:
    """Build a chat history that is safe to send to ai-gateway.

    Args:
        chat_id (str): The chat whose messages should be inspected.
        exclude_last_content (str | None): Optional anonymized content to
            exclude from the end of the history because it will be sent as the
            current prompt.

    Returns:
        list[OrchestratorChatHistoryMessage]: Previous messages containing only
            anonymized content.
    """
    chat = container.chat_repository.load_chat(chat_id)
    if chat is None:
        raise KeyError(chat_id)

    messages = [
        message
        for message in chat.messages
        if message.anonymized_content and message.anonymized_content.strip()
    ]
    if (
        exclude_last_content is not None
        and messages
        and messages[-1].anonymized_content == exclude_last_content
    ):
        messages = messages[:-1]

    return [
        OrchestratorChatHistoryMessage(
            role=message.role,
            content=message.anonymized_content or "",
        )
        for message in messages
    ]


def _get_model_readiness() -> dict[str, object]:
    """Return whether the required backend models are loaded.

    Returns:
        dict[str, object]: The model readiness payload consumed by the UI.
    """
    model_names = [PRIVACY_MODEL_NAME]
    if DOCUMENT_MODEL_NAME != PRIVACY_MODEL_NAME:
        model_names.append(DOCUMENT_MODEL_NAME)

    statuses: dict[str, str] = {}
    try:
        with httpx.Client(
            base_url=MODEL_PROVIDER_BASE_URL,
            timeout=MODEL_STATUS_TIMEOUT_SECONDS,
        ) as client:
            for model_name in model_names:
                response = client.get(
                    "/model_status",
                    params={"name": model_name},
                )
                response.raise_for_status()
                statuses[model_name] = str(response.json())
    except httpx.HTTPError as error:
        return {
            "ready": False,
            "message": "El proveedor de modelos aún no está disponible.",
            "detail": str(error),
            "models": statuses,
        }

    missing_models = [
        name
        for name, status_text in statuses.items()
        if " is loaded." not in status_text
    ]
    if missing_models:
        return {
            "ready": False,
            "message": "Cargando modelos de GuardianAI...",
            "models": statuses,
        }

    return {
        "ready": True,
        "message": "Modelos listos.",
        "models": statuses,
    }
