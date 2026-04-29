"""FastAPI entrypoint for the GuardianAI orchestrator module."""
from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

import uvicorn
from fastapi import FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from infrastructure.adapters.fake_assistant_stream_gateway import (
    FakeAssistantStreamGateway,
)
from infrastructure.adapters.http_privacy_shield_client import (
    HttpPrivacyShieldClient,
    PrivacyShieldClientError,
)
from infrastructure.adapters.http_document_processing_client import (
    DocumentProcessorClientError,
    DocumentUpload,
    HttpDocumentProcessingClient,
)


class MessageStreamRequest(BaseModel):
    """Represent a prompt stream request from web-ui.

    Attributes:
        chat_id (str): The chat that will display the response.
        text (str): The original user prompt.
    """

    chat_id: str = Field(min_length=1)
    text: str = Field(min_length=1)


@dataclass(frozen=True)
class OrchestratorContainer:
    """Group the orchestrator dependencies.

    Attributes:
        privacy_shield (HttpPrivacyShieldClient): The privacy-shield client.
        document_processor (HttpDocumentProcessingClient): The document
            processor client.
        assistant_gateway (FakeAssistantStreamGateway): The temporary assistant.
    """

    privacy_shield: HttpPrivacyShieldClient
    document_processor: HttpDocumentProcessingClient
    assistant_gateway: FakeAssistantStreamGateway


def build_container() -> OrchestratorContainer:
    """Build the orchestrator dependency graph.

    Returns:
        OrchestratorContainer: The configured dependency container.
    """
    return OrchestratorContainer(
        privacy_shield=HttpPrivacyShieldClient(),
        document_processor=HttpDocumentProcessingClient(),
        assistant_gateway=FakeAssistantStreamGateway(),
    )


processed_documents: dict[str, str] = {}
container = build_container()
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
    """Coordinate prompt anonymization, fake assistant, and deanonymization.

    Args:
        payload (MessageStreamRequest): The prompt stream request from web-ui.

    Returns:
        StreamingResponse: The safe NDJSON stream consumed by web-ui.
    """
    try:
        anonymized_prompt = container.privacy_shield.anonymize(
            chat_id=payload.chat_id,
            text=payload.text,
        )
        assistant_chunks = list(
            container.assistant_gateway.stream_response(
                anonymized_prompt.text
            )
        )
        events = container.privacy_shield.deanonymize_stream(
            chunks=assistant_chunks,
            replacements=anonymized_prompt.replacements,
        )
    except PrivacyShieldClientError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error

    return _build_streaming_response(events)


@app.post("/api/documents/extract-stream")
async def extract_document_stream(
    file: UploadFile = File(...),
) -> StreamingResponse:
    """Forward a document upload to document-processor.

    Args:
        file (UploadFile): The uploaded PDF file.

    Returns:
        StreamingResponse: The document processing NDJSON stream.
    """
    filename = file.filename or "document.pdf"
    content_type = file.content_type or ""
    content = await file.read()

    try:
        events = container.document_processor.stream_extract_document(
            DocumentUpload(
                filename=filename,
                content_type=content_type,
                content=content,
            )
        )
    except DocumentProcessorClientError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error

    return _build_document_streaming_response(events)


@app.post("/api/documents/safe-stream")
def stream_document_response(payload: dict[str, str]) -> StreamingResponse:
    """Generate a safe response for a processed document.

    Args:
        payload (dict[str, str]): The chat and document identifiers.

    Returns:
        StreamingResponse: The safe NDJSON stream consumed by web-ui.

    Raises:
        HTTPException: If the document is unknown or privacy-shield fails.
    """
    chat_id = payload.get("chat_id", "").strip()
    document_id = payload.get("document_id", "").strip()
    if not chat_id or not document_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="chat_id and document_id are required.",
        )

    extracted_text = processed_documents.get(document_id)
    if extracted_text is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Processed document not found.",
        )

    try:
        events = _stream_safe_response_for_text(
            chat_id=chat_id,
            text=extracted_text,
        )
    except PrivacyShieldClientError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error

    return _build_streaming_response(events)


def _build_streaming_response(
    events: Iterator[dict[str, Any]],
) -> StreamingResponse:
    """Serialize downstream stream events as NDJSON.

    Args:
        events (Iterator[dict[str, Any]]): Downstream stream events.

    Returns:
        StreamingResponse: The serialized NDJSON response.
    """
    def event_stream() -> Iterator[str]:
        """Yield stream events as JSON lines.

        Yields:
            str: One JSON-encoded event followed by a newline.
        """
        try:
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


def _stream_safe_response_for_text(
    chat_id: str,
    text: str,
) -> Iterator[dict[str, Any]]:
    """Run the text through privacy-shield, fake assistant, and restoration.

    Args:
        chat_id (str): The chat that owns the request.
        text (str): The original text to protect and answer.

    Returns:
        Iterator[dict[str, Any]]: Safe response stream events.
    """
    anonymized_prompt = container.privacy_shield.anonymize(
        chat_id=chat_id,
        text=text,
    )
    assistant_chunks = list(
        container.assistant_gateway.stream_response(anonymized_prompt.text)
    )
    return container.privacy_shield.deanonymize_stream(
        chunks=assistant_chunks,
        replacements=anonymized_prompt.replacements,
    )


def _build_document_streaming_response(
    events: Iterator[dict[str, Any]],
) -> StreamingResponse:
    """Serialize document processor events as NDJSON.

    Args:
        events (Iterator[dict[str, Any]]): Document processor events.

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
                if event.get("event") == "completed":
                    document_id = str(event.get("document_id", ""))
                    extracted_text = str(event.get("extracted_text", ""))
                    if document_id:
                        processed_documents[document_id] = extracted_text

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


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7003)
