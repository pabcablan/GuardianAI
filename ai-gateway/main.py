"""HTTP entrypoint for the ai-gateway service."""
from __future__ import annotations

import json
import logging
import os
from collections.abc import AsyncGenerator
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
import uvicorn

from application.body_params_schemas.chat_request import ChatRequest
from application.usecases.send_to_llm import SendToLLM
from domain.exceptions import (
    ProviderAPIError,
    ProviderConnectionError,
    ProviderRateLimitError,
)
from domain.value_objects.anonymized_text import AnonymizedText
from domain.value_objects.message import Message, Role
from infrastructure.adapters.file_audit_log import FileAuditLog
from infrastructure.adapters.openai_language_model import OpenAILanguageModel


LOGGER = logging.getLogger(__name__)

CURRENT_DIR = Path(__file__).parent
load_dotenv(CURRENT_DIR / ".env")
load_dotenv(CURRENT_DIR.parent / ".env")

API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise RuntimeError(
        "OPENAI_API_KEY is required to start the ai-gateway service."
    )

app = FastAPI(
    title="GuardianAI AI Gateway",
    version="0.1.0",
    description="Streams assistant responses through a provider adapter.",
)

language_model = OpenAILanguageModel(api_key=API_KEY)
audit_log = FileAuditLog(file_path=str(CURRENT_DIR / "audit.log"))
send_to_llm = SendToLLM(
    language_model=language_model,
    audit_log=audit_log,
)


def _build_sse_data(payload: str) -> str:
    """Serialize one text chunk as a safe SSE payload."""
    return json.dumps(
        {
            "type": "chunk",
            "content": payload,
        },
        ensure_ascii=False,
    )


def _build_error_event(status_code: int, detail: str) -> str:
    """Build one SSE error event payload."""
    return f"data: error:{status_code}:{detail}\n\n"


def _build_messages(request: ChatRequest) -> list[Message]:
    """Convert one HTTP request payload into domain messages."""
    return [
        Message(
            role=Role(item.role),
            content=AnonymizedText(item.content),
        )
        for item in request.messages
    ]


@app.post("/handle")
async def handle(request: ChatRequest) -> StreamingResponse:
    """Stream model output as a server-sent events response.

    Args:
        request (ChatRequest): The incoming chat request.

    Returns:
        StreamingResponse: The SSE stream consumed by orchestrator.
    """
    try:
        messages = _build_messages(request)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    async def event_stream() -> AsyncGenerator[str, None]:
        try:
            async for chunk in send_to_llm.stream(
                messages,
                request.model,
            ):
                yield f"data: {_build_sse_data(chunk)}\n\n"
            yield "data: [DONE]\n\n"
        except ProviderRateLimitError as error:
            LOGGER.warning("AI gateway rate limit error: %s", error)
            yield _build_error_event(429, str(error))
        except ProviderConnectionError as error:
            LOGGER.warning("AI gateway connection error: %s", error)
            yield _build_error_event(503, str(error))
        except ProviderAPIError as error:
            LOGGER.warning("AI gateway provider API error: %s", error)
            yield _build_error_event(502, str(error))

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def main() -> None:
    """Run the ai-gateway development server."""
    uvicorn.run(app, host="0.0.0.0", port=8005)


if __name__ == "__main__":
    main()
