"""NDJSON streaming helpers for the web-ui API."""
from __future__ import annotations

import json
from collections.abc import Callable, Iterator

from fastapi.responses import StreamingResponse

from domain.message import Message
from infrastructure.adapters.api.schemas import (
    AttachDocumentCompletedResponse,
    AttachDocumentErrorResponse,
    AttachDocumentProgressResponse,
    SafeStreamAnonymizedPromptResponse,
    SafeStreamChunkResponse,
    SafeStreamCompletedResponse,
    SafeStreamErrorResponse,
)
from infrastructure.ports.external.orchestrator_response_port import (
    OrchestratorAnonymizedResponse,
    OrchestratorAnonymizedPrompt,
    OrchestratorStreamChunk,
    OrchestratorStreamCompleted,
    OrchestratorStreamEvent,
    OrchestratorStreamFailed,
)
from infrastructure.ports.internal.chat_repository_port import (
    ChatRepositoryPort,
)


AssistantMessageFactory = Callable[[str, str | None], Message]


def build_safe_streaming_response(
    events: Iterator[OrchestratorStreamEvent],
    chat_repository: ChatRepositoryPort,
    make_assistant_message: AssistantMessageFactory,
    chat_id: str | None = None,
    user_message_id: str | None = None,
) -> StreamingResponse:
    """Build an NDJSON response from orchestrator stream events.

    Args:
        events (Iterator[OrchestratorStreamEvent]): The stream events.
        chat_repository (ChatRepositoryPort): The chat storage gateway.
        make_assistant_message (AssistantMessageFactory): Factory used to
            create persisted assistant messages.
        chat_id (str | None): The chat identifier to persist into.
        user_message_id (str | None): The user message that owns anonymized
            content.

    Returns:
        StreamingResponse: The serialized safe stream.
    """

    def event_stream() -> Iterator[str]:
        """Serialize safe stream events as JSON lines.

        Yields:
            str: One JSON-encoded event followed by a newline.
        """
        assistant_chunks: list[str] = []
        assistant_anonymized_content: str | None = None
        did_complete = False

        try:
            for event in events:
                if isinstance(event, OrchestratorStreamChunk):
                    assistant_chunks.append(event.content)
                    payload = SafeStreamChunkResponse(
                        content=event.content,
                    ).model_dump()
                elif isinstance(event, OrchestratorAnonymizedPrompt):
                    if user_message_id is not None:
                        chat_repository.update_message_anonymized_content(
                            user_message_id,
                            event.content,
                        )
                    payload = SafeStreamAnonymizedPromptResponse(
                        content=event.content,
                    ).model_dump()
                elif isinstance(event, OrchestratorAnonymizedResponse):
                    assistant_anonymized_content = event.content
                    continue
                elif isinstance(event, OrchestratorStreamCompleted):
                    did_complete = True
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

            if did_complete:
                _persist_assistant_message(
                    chat_repository=chat_repository,
                    make_assistant_message=make_assistant_message,
                    chat_id=chat_id,
                    content="".join(assistant_chunks),
                    anonymized_content=assistant_anonymized_content,
                )
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


def build_document_streaming_response(
    events: Iterator[object],
    remember_user_message: Callable[[str], None],
) -> StreamingResponse:
    """Build an NDJSON response for document attachment events.

    Args:
        events (Iterator[object]): The document attachment events.
        remember_user_message (Callable[[str], None]): Callback that stores
            the completed document identifier.

    Returns:
        StreamingResponse: The serialized document stream.
    """

    from application.usecases.attach_document import (
        AttachDocumentCompleted,
        AttachDocumentFailed,
        AttachDocumentProgress,
    )

    def event_stream() -> Iterator[str]:
        """Serialize document processing events as JSON lines.

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
                    remember_user_message(event.document_id)
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


def _persist_assistant_message(
    chat_repository: ChatRepositoryPort,
    make_assistant_message: AssistantMessageFactory,
    chat_id: str | None,
    content: str,
    anonymized_content: str | None,
) -> None:
    """Persist the final assistant response when a stream finishes.

    Args:
        chat_repository (ChatRepositoryPort): The chat storage gateway.
        make_assistant_message (AssistantMessageFactory): Factory used to
            create an assistant message.
        chat_id (str | None): The chat that owns the response.
        content (str): The accumulated assistant content.
        anonymized_content (str | None): The accumulated assistant content
            before deanonymization.
    """
    if chat_id is None or not content.strip():
        return

    chat_repository.append_message(
        chat_id,
        make_assistant_message(content, anonymized_content),
    )
