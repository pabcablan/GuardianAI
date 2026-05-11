"""FastAPI entrypoint for the GuardianAI orchestrator module."""
from __future__ import annotations

from typing import Any

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse

from application.orchestration_service import OrchestrationService
from infrastructure.adapters.api.errors import (
    bad_gateway,
    processed_document_not_found,
)
from infrastructure.adapters.api.payloads import (
    build_anonymized_preview_payload,
    build_anonymized_prompt_event,
)
from infrastructure.adapters.api.schemas import (
    AnonymizedStreamRequest,
    DocumentPreviewRequest,
    MessageStreamRequest,
)
from infrastructure.adapters.api.streaming import (
    build_document_streaming_response,
    build_streaming_response,
)
from infrastructure.adapters.http.ai_gateway_client import AiGatewayClientError
from infrastructure.adapters.http.document_processor_client import (
    DocumentProcessorClientError,
)
from infrastructure.adapters.http.privacy_shield_client import (
    PrivacyShieldClientError,
)
from infrastructure.dependency_container import build_container
from infrastructure.ports.ai_gateway_port import AssistantMessage


container = build_container()
orchestration_service = OrchestrationService(container)

app = FastAPI(
    title="GuardianAI Orchestrator",
    version="0.1.0",
    description="Coordinates GuardianAI services for web-ui.",
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
    """Return the orchestrator health status.

    Returns:
        dict[str, str]: A simple status payload.
    """
    return {"status": "ok"}


@app.post("/api/messages/stream")
def stream_message_response(payload: MessageStreamRequest) -> StreamingResponse:
    """Coordinate prompt anonymization, assistant, and deanonymization.

    Args:
        payload (MessageStreamRequest): The prompt stream request from web-ui.

    Returns:
        StreamingResponse: The safe NDJSON stream consumed by web-ui.
    """
    try:
        anonymized_prompt, events = (
            orchestration_service.stream_message_response(
                chat_id=payload.chat_id,
                text=payload.text,
                model=payload.model,
                history=_build_assistant_history(payload.history),
            )
        )
    except (AiGatewayClientError, PrivacyShieldClientError) as error:
        raise bad_gateway(error) from error

    return build_streaming_response(
        events,
        initial_events=[build_anonymized_prompt_event(anonymized_prompt)],
    )


@app.post("/api/messages/anonymize-preview")
def preview_message_anonymization(
    payload: MessageStreamRequest,
) -> dict[str, Any]:
    """Return the anonymized prompt without calling the assistant.

    Args:
        payload (MessageStreamRequest): The prompt to anonymize.

    Returns:
        dict[str, Any]: The anonymized prompt metadata.
    """
    try:
        anonymized_prompt = (
            orchestration_service.preview_message_anonymization(
                chat_id=payload.chat_id,
                text=payload.text,
            )
        )
    except PrivacyShieldClientError as error:
        raise bad_gateway(error) from error

    return build_anonymized_preview_payload(anonymized_prompt)


@app.post("/api/documents/anonymize-preview")
def preview_document_anonymization(
    payload: DocumentPreviewRequest,
) -> dict[str, Any]:
    """Return the anonymized document prompt without calling the assistant.

    Args:
        payload (DocumentPreviewRequest): The processed document identifiers.

    Returns:
        dict[str, Any]: The anonymized document prompt metadata.
    """
    try:
        anonymized_prompt = (
            orchestration_service.preview_document_anonymization(
                chat_id=payload.chat_id,
                document_id=payload.document_id,
            )
        )
    except KeyError as error:
        raise processed_document_not_found() from error
    except ValueError as error:
        raise _unprocessable_entity(error) from error
    except PrivacyShieldClientError as error:
        raise bad_gateway(error) from error

    return build_anonymized_preview_payload(anonymized_prompt)


@app.post("/api/anonymized/stream")
def stream_anonymized_response(
    payload: AnonymizedStreamRequest,
) -> StreamingResponse:
    """Call the assistant with already anonymized text and restore the answer.

    Args:
        payload (AnonymizedStreamRequest): The anonymized prompt data.

    Returns:
        StreamingResponse: The safe NDJSON stream consumed by web-ui.
    """
    try:
        events = orchestration_service.stream_anonymized_response(
            chat_id=payload.chat_id,
            anonymized_text=payload.anonymized_text,
            anonymization_id=payload.anonymization_id,
            model=payload.model,
            history=_build_assistant_history(payload.history),
        )
    except (AiGatewayClientError, PrivacyShieldClientError) as error:
        raise bad_gateway(error) from error
    except ValueError as error:
        raise _unprocessable_entity(error) from error

    return build_streaming_response(events)


@app.post("/api/documents/extract-stream")
async def extract_document_stream(
    file: UploadFile = File(...),
    prompt: str = Form(""),
) -> StreamingResponse:
    """Forward a document upload to document-processor.

    Args:
        file (UploadFile): The uploaded PDF file.
        prompt (str): The optional prompt to combine with the extracted text.

    Returns:
        StreamingResponse: The document processing NDJSON stream.
    """
    filename = file.filename or "document.pdf"
    content_type = file.content_type or ""
    content = await file.read()

    try:
        events = orchestration_service.stream_extract_document(
            filename=filename,
            content_type=content_type,
            content=content,
        )
    except DocumentProcessorClientError as error:
        raise bad_gateway(error) from error

    def store_document(event: dict[str, Any]) -> None:
        """Store a completed document processing event."""
        orchestration_service.store_document_if_completed(
            event=event,
            prompt=prompt,
            filename=filename,
            content_type=content_type,
            content=content,
        )

    return build_document_streaming_response(
        events,
        store_document=store_document,
    )


@app.post("/api/documents/safe-stream")
def stream_document_response(payload: dict[str, str]) -> StreamingResponse:
    """Generate a safe response for a processed document.

    Args:
        payload (dict[str, str]): The chat and document identifiers.

    Returns:
        StreamingResponse: The safe NDJSON stream consumed by web-ui.
    """
    chat_id = payload.get("chat_id", "").strip()
    document_id = payload.get("document_id", "").strip()
    model = payload.get("model", "").strip()
    if not chat_id or not document_id or not model:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="chat_id, document_id, and model are required.",
        )

    try:
        anonymized_prompt, events = (
            orchestration_service.stream_document_response(
                chat_id=chat_id,
                document_id=document_id,
                model=model,
            )
        )
    except KeyError as error:
        raise processed_document_not_found() from error
    except ValueError as error:
        raise _unprocessable_entity(error) from error
    except (AiGatewayClientError, PrivacyShieldClientError) as error:
        raise bad_gateway(error) from error

    return build_streaming_response(
        events,
        initial_events=[build_anonymized_prompt_event(anonymized_prompt)],
    )


@app.get("/api/documents/{document_id}/anonymized-pdf-preview")
def download_anonymized_pdf_preview(
    document_id: str,
    anonymization_id: str,
) -> Response:
    """Return a visual anonymized PDF preview when possible.

    Args:
        document_id (str): The processed document identifier.
        anonymization_id (str): The anonymization session identifier.

    Returns:
        Response: The generated anonymized PDF bytes.
    """
    try:
        preview = orchestration_service.build_anonymized_pdf_preview(
            document_id=document_id,
            anonymization_id=anonymization_id,
        )
    except KeyError as error:
        raise processed_document_not_found() from error
    except ValueError as error:
        raise _unprocessable_entity(error) from error

    return Response(
        content=preview.content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{preview.filename}"',
        },
    )


def _unprocessable_entity(error: Exception) -> HTTPException:
    """Build an unprocessable entity response from an application error.

    Args:
        error (Exception): The application error.

    Returns:
        HTTPException: The HTTP 422 error.
    """
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=str(error),
    )


def _build_assistant_history(history: list[Any]) -> list[AssistantMessage]:
    """Convert API history payloads into assistant messages.

    Args:
        history (list[Any]): The Pydantic history items received by the API.

    Returns:
        list[AssistantMessage]: Messages safe to forward to ai-gateway.
    """
    return [
        AssistantMessage(
            role=item.role,
            content=item.content,
        )
        for item in history
    ]


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
