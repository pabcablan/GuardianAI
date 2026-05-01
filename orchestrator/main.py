"""FastAPI entrypoint for the GuardianAI orchestrator module."""
from __future__ import annotations

import json
import time
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from infrastructure.adapters.http.ai_gateway_client import (
    AiGatewayClientError,
    HttpAiGatewayClient,
)
from infrastructure.adapters.http.privacy_shield_client import (
    HttpPrivacyShieldClient,
    PrivacyShieldClientError,
)
from infrastructure.adapters.http.document_processor_client import (
    DocumentProcessorClientError,
    HttpDocumentProcessingClient,
)
from infrastructure.ports.ai_gateway_port import (
    AiGatewayPort,
    AssistantStreamRequest,
)
from infrastructure.ports.document_processor_port import (
    DocumentProcessorPort,
    DocumentUploadRequest,
)
from infrastructure.ports.privacy_shield_port import PrivacyShieldPort


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
        privacy_shield (PrivacyShieldPort): The privacy-shield client.
        document_processor (DocumentProcessorPort): The document processor
            client.
        ai_gateway (AiGatewayPort): The assistant stream gateway.
    """

    privacy_shield: PrivacyShieldPort
    document_processor: DocumentProcessorPort
    ai_gateway: AiGatewayPort


@dataclass(frozen=True)
class ProcessedDocumentContext:
    """Store the extracted document text and the optional user prompt.

    Attributes:
        extracted_text (str): The text returned by document-processor.
        prompt (str): The optional prompt sent with the uploaded document.
    """

    extracted_text: str
    prompt: str = ""


def build_container() -> OrchestratorContainer:
    """Build the orchestrator dependency graph.

    Returns:
        OrchestratorContainer: The configured dependency container.
    """
    return OrchestratorContainer(
        privacy_shield=HttpPrivacyShieldClient(),
        document_processor=HttpDocumentProcessingClient(),
        ai_gateway=HttpAiGatewayClient(),
    )


processed_documents: dict[str, ProcessedDocumentContext] = {}
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
    started_at = time.perf_counter()
    print(
        "ORCHESTRATOR /api/messages/stream "
        f"chat_id={payload.chat_id} text_len={len(payload.text)}",
        flush=True,
    )
    try:
        step_started_at = time.perf_counter()
        anonymized_prompt = container.privacy_shield.anonymize(
            chat_id=payload.chat_id,
            text=payload.text,
        )
        print(
            "ORCHESTRATOR anonymize done "
            f"elapsed={time.perf_counter() - step_started_at:.3f}s "
            f"replacement_count={len(anonymized_prompt.replacements)}",
            flush=True,
        )
        step_started_at = time.perf_counter()
        assistant_chunks = _collect_ai_gateway_chunks(
            chat_id=payload.chat_id,
            anonymized_prompt=anonymized_prompt.text,
        )
        print(
            "ORCHESTRATOR ai-gateway done "
            f"elapsed={time.perf_counter() - step_started_at:.3f}s "
            f"chunk_count={len(assistant_chunks)}",
            flush=True,
        )
        step_started_at = time.perf_counter()
        events = container.privacy_shield.deanonymize_stream(
            chunks=assistant_chunks,
            replacements=anonymized_prompt.replacements,
        )
        print(
            "ORCHESTRATOR deanonymize requested "
            f"elapsed={time.perf_counter() - step_started_at:.3f}s "
            f"total_before_stream={time.perf_counter() - started_at:.3f}s",
            flush=True,
        )
    except (AiGatewayClientError, PrivacyShieldClientError) as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error

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
        events = container.document_processor.stream_extract_document(
            DocumentUploadRequest(
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

    return _build_document_streaming_response(events, prompt=prompt)


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

    document_context = processed_documents.get(document_id)
    if document_context is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Processed document not found.",
        )

    text = _build_document_prompt(document_context)
    if not text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Document processor returned empty text and no prompt was "
                "provided."
            ),
        )

    try:
        events = _stream_safe_response_for_text(
            chat_id=chat_id,
            text=text,
        )
    except (AiGatewayClientError, PrivacyShieldClientError) as error:
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
    started_at = time.perf_counter()
    anonymized_prompt = container.privacy_shield.anonymize(
        chat_id=chat_id,
        text=text,
    )
    print(
        "ORCHESTRATOR document anonymize done "
        f"elapsed={time.perf_counter() - started_at:.3f}s "
        f"replacement_count={len(anonymized_prompt.replacements)}",
        flush=True,
    )
    started_at = time.perf_counter()
    assistant_chunks = _collect_ai_gateway_chunks(
        chat_id=chat_id,
        anonymized_prompt=anonymized_prompt.text,
    )
    print(
        "ORCHESTRATOR document ai-gateway done "
        f"elapsed={time.perf_counter() - started_at:.3f}s "
        f"chunk_count={len(assistant_chunks)}",
        flush=True,
    )
    return container.privacy_shield.deanonymize_stream(
        chunks=assistant_chunks,
        replacements=anonymized_prompt.replacements,
    )


def _collect_ai_gateway_chunks(
    chat_id: str,
    anonymized_prompt: str,
) -> list[str]:
    """Collect assistant chunks from the configured ai-gateway.

    Args:
        chat_id (str): The chat that owns the request.
        anonymized_prompt (str): The anonymized prompt sent to the assistant.

    Returns:
        list[str]: The anonymized assistant response chunks.
    """
    return [
        chunk
        for chunk in container.ai_gateway.stream_response(
            AssistantStreamRequest(
                chat_id=chat_id,
                prompt=anonymized_prompt,
            )
        )
        if chunk
    ]


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
                if event.get("event") == "completed":
                    document_id = str(event.get("document_id", ""))
                    extracted_text = str(event.get("extracted_text", ""))
                    if document_id:
                        processed_documents[document_id] = (
                            ProcessedDocumentContext(
                                extracted_text=extracted_text,
                                prompt=prompt.strip(),
                            )
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


def _build_document_prompt(document_context: ProcessedDocumentContext) -> str:
    """Build the text that enters the safe response pipeline.

    Args:
        document_context (ProcessedDocumentContext): The stored document data.

    Returns:
        str: The prompt-only, document-only, or combined prompt text.
    """
    prompt = document_context.prompt.strip()
    extracted_text = document_context.extracted_text.strip()

    if prompt and extracted_text:
        return (
            "User prompt:\n"
            f"{prompt}\n\n"
            "Document text:\n"
            f"{extracted_text}"
        )

    return prompt or extracted_text


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
