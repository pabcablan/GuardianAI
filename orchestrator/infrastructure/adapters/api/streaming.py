"""Streaming response helpers for the orchestrator API."""
from __future__ import annotations

import json
from collections.abc import Callable, Iterator
from typing import Any

from fastapi.responses import StreamingResponse


def build_streaming_response(
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
            yield _build_error_event(error)

    return _ndjson_response(event_stream())


def build_document_streaming_response(
    events: Iterator[dict[str, Any]],
    store_document: Callable[[dict[str, Any]], None],
) -> StreamingResponse:
    """Serialize document processor events as NDJSON.

    Args:
        events (Iterator[dict[str, Any]]): Document processor events.
        store_document (Callable[[dict[str, Any]], None]): Callback used to
            store completed document data.

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
                store_document(event)
                yield json.dumps(event, ensure_ascii=True) + "\n"
        except RuntimeError as error:
            yield _build_error_event(error)

    return _ndjson_response(event_stream())


def _ndjson_response(events: Iterator[str]) -> StreamingResponse:
    """Build a standard NDJSON streaming response.

    Args:
        events (Iterator[str]): Serialized NDJSON lines.

    Returns:
        StreamingResponse: The configured streaming response.
    """
    return StreamingResponse(
        events,
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


def _build_error_event(error: RuntimeError) -> str:
    """Serialize a runtime stream error as NDJSON.

    Args:
        error (RuntimeError): The runtime error.

    Returns:
        str: A serialized error event.
    """
    return json.dumps(
        {
            "event": "error",
            "detail": str(error),
        },
        ensure_ascii=True,
    ) + "\n"
