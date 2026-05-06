"""FastAPI entrypoint for the GuardianAI orchestrator module."""
from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from application.orchestration_service import OrchestrationService
from infrastructure.adapters.api.schemas import (
    AnonymizedStreamRequest,
    DocumentPreviewRequest,
    MessageStreamRequest,
)
from infrastructure.adapters.http.ai_gateway_client import AiGatewayClientError
from infrastructure.adapters.http.document_processor_client import (
    DocumentProcessorClientError,
)
from infrastructure.adapters.http.privacy_shield_client import (
    PrivacyShieldClientError,
)
from infrastructure.dependency_container import build_container
from infrastructure.ports.privacy_shield_port import AnonymizedPrompt


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
            )
        )
    except (AiGatewayClientError, PrivacyShieldClientError) as error:
        raise _bad_gateway(error) from error

    return _build_streaming_response(
        events,
        initial_events=[_build_anonymized_prompt_event(anonymized_prompt)],
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
        raise _bad_gateway(error) from error

    return _build_anonymized_preview_payload(anonymized_prompt)


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
        raise _processed_document_not_found() from error
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error
    except PrivacyShieldClientError as error:
        raise _bad_gateway(error) from error

    return _build_anonymized_preview_payload(anonymized_prompt)


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
        )
    except (AiGatewayClientError, PrivacyShieldClientError) as error:
        raise _bad_gateway(error) from error

    return _build_streaming_response(events)


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
        raise _bad_gateway(error) from error

    return _build_document_streaming_response(events, prompt=prompt)


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
        raise _processed_document_not_found() from error
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error
    except (AiGatewayClientError, PrivacyShieldClientError) as error:
        raise _bad_gateway(error) from error

    return _build_streaming_response(
        events,
        initial_events=[_build_anonymized_prompt_event(anonymized_prompt)],
    )


def _build_streaming_response(
    events: Iterator[dict[str, Any]],
    initial_events: list[dict[str, Any]] | None = None,
) -> StreamingResponse:
    """Serialize downstream stream events as NDJSON.

    Args:
        events (Iterator[dict[str, Any]]): Downstream stream events.
        initial_events (list[dict[str, Any]] | None): Events emitted before
            downstream streaming starts.

    Returns:
        StreamingResponse: The serialized NDJSON response.
    """
    def event_stream() -> Iterator[str]:
        """Yield stream events as JSON lines.

        Yields:
            str: One JSON-encoded event followed by a newline.
        """
        try:
            for event in initial_events or []:
                yield json.dumps(event, ensure_ascii=True) + "\n"

            for event in events:
                yield json.dumps(event, ensure_ascii=True) + "\n"
        except RuntimeError as error:
            yield json.dumps(
                {
                    "event": "error",
                    "detail": str(error),
                },
                ensure_ascii=True,
            ) + "\n"

    return StreamingResponse(
        event_stream(),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


def _build_document_streaming_response(
    events: Iterator[dict[str, Any]],
    prompt: str,
) -> StreamingResponse:
    """Serialize document processor events as NDJSON.

    Args:
        events (Iterator[dict[str, Any]]): Document processor events.
        prompt (str): The optional prompt sent with the document.

    Returns:
        StreamingResponse: The serialized NDJSON response.
    """
    def event_stream() -> Iterator[str]:
        """Yield document processor events as JSON lines.

        Yields:
            str: One JSON-encoded event followed by a newline.
        """
        try:
            for event in events:
                orchestration_service.store_document_if_completed(
                    event=event,
                    prompt=prompt,
                )
                yield json.dumps(event, ensure_ascii=True) + "\n"
        except RuntimeError as error:
            yield json.dumps(
                {
                    "event": "error",
                    "detail": str(error),
                },
                ensure_ascii=True,
            ) + "\n"

    return StreamingResponse(
        event_stream(),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


def _build_anonymized_prompt_event(
    anonymized_prompt: AnonymizedPrompt,
) -> dict[str, str]:
    """Build the stream event that exposes anonymized text to web-ui.

    Args:
        anonymized_prompt (AnonymizedPrompt): The anonymized prompt metadata.

    Returns:
        dict[str, str]: The stream event payload.
    """
    return {
        "event": "anonymized_prompt",
        "content": anonymized_prompt.text,
    }


def _build_anonymized_preview_payload(
    anonymized_prompt: AnonymizedPrompt,
) -> dict[str, Any]:
    """Build the API payload for anonymization previews.

    Args:
        anonymized_prompt (AnonymizedPrompt): The anonymized prompt metadata.

    Returns:
        dict[str, Any]: The preview payload.
    """
    return {
        "anonymized_text": anonymized_prompt.text,
        "anonymization_id": anonymized_prompt.anonymization_id,
        "replacement_count": anonymized_prompt.replacement_count,
    }


def _processed_document_not_found() -> HTTPException:
    """Build the processed-document-not-found HTTP error.

    Returns:
        HTTPException: The HTTP 404 error.
    """
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Processed document not found.",
    )


def _bad_gateway(error: Exception) -> HTTPException:
    """Build a bad gateway error for downstream service failures.

    Args:
        error (Exception): The downstream service error.

    Returns:
        HTTPException: The HTTP 502 error.
    """
    return HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=str(error),
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
