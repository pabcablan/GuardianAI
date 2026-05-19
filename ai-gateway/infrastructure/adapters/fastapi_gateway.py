"""FastAPI adapter that exposes the ai-gateway streaming endpoint."""
from __future__ import annotations

import json
import logging
from collections.abc import AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from application.body_params_schemas.chat_request import ChatRequest
from application.usecases.send_to_llm import SendToLLM
from domain.exceptions import (
    ProviderAPIError,
    ProviderConnectionError,
    ProviderRateLimitError,
)
from domain.value_objects.anonymized_text import AnonymizedText
from domain.value_objects.message import Message, Role


LOGGER = logging.getLogger(__name__)


class FastAPIGateway:
    """Expose the streaming HTTP contract for ai-gateway."""

    def __init__(self, send_to_llm: SendToLLM) -> None:
        """Initialize the gateway router.

        Args:
            send_to_llm (SendToLLM): The use case that streams model output.
        """
        self._send_to_llm = send_to_llm
        self._router = APIRouter()
        self._router.add_api_route("/handle", self.handle, methods=["POST"])

    @property
    def router(self) -> APIRouter:
        """Return the configured FastAPI router.

        Returns:
            APIRouter: The HTTP router exposed by the gateway.
        """
        return self._router

    @staticmethod
    def _build_sse_data(payload: str) -> str:
        """Serialize one text chunk as a safe SSE payload.

        Args:
            payload (str): The generated response chunk.

        Returns:
            str: The serialized SSE data payload.
        """
        return json.dumps(
            {
                "type": "chunk",
                "content": payload,
            },
            ensure_ascii=False,
        )

    @staticmethod
    def _build_error_event(status_code: int, detail: str) -> str:
        """Build one SSE error event payload.

        Args:
            status_code (int): The provider-facing status code.
            detail (str): The error detail.

        Returns:
            str: The serialized SSE error event.
        """
        return f"data: error:{status_code}:{detail}\n\n"

    @staticmethod
    def _build_messages(request: ChatRequest) -> list[Message]:
        """Convert one HTTP request payload into domain messages.

        Args:
            request (ChatRequest): The incoming chat request.

        Returns:
            list[Message]: The normalized domain messages.
        """
        return [
            Message(
                role=Role(item.role),
                content=AnonymizedText(item.content),
            )
            for item in request.messages
        ]

    async def handle(self, request: ChatRequest) -> StreamingResponse:
        """Stream model output as a server-sent events response.

        Args:
            request (ChatRequest): The incoming chat request.

        Returns:
            StreamingResponse: The SSE stream consumed by orchestrator.
        """
        try:
            messages = self._build_messages(request)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error))

        async def event_stream() -> AsyncGenerator[str, None]:
            try:
                async for chunk in self._send_to_llm.stream(
                    messages,
                    request.model,
                ):
                    yield f"data: {self._build_sse_data(chunk)}\n\n"
                yield "data: [DONE]\n\n"
            except ProviderRateLimitError as error:
                LOGGER.warning("AI gateway rate limit error: %s", error)
                yield self._build_error_event(429, str(error))
            except ProviderConnectionError as error:
                LOGGER.warning("AI gateway connection error: %s", error)
                yield self._build_error_event(503, str(error))
            except ProviderAPIError as error:
                LOGGER.warning("AI gateway provider API error: %s", error)
                yield self._build_error_event(502, str(error))

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
