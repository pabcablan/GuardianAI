import json
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

import uvicorn
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field


ANONYMIZATION_DEBUG_PATH = (
    Path(__file__).resolve().parent / "storage" / "anonymization_debug.jsonl"
)


class AnonymizeRequest(BaseModel):
    """Represent a prompt anonymization request.

    Attributes:
        chat_id (str): The chat that produced the prompt.
        text (str): The original user prompt to anonymize.
    """

    chat_id: str = Field(min_length=1)
    text: str = Field(min_length=1)


class DeanonymizeStreamRequest(BaseModel):
    """Represent a streamed assistant response to restore.

    Attributes:
        chunks (list[str]): The anonymized assistant chunks to restore.
        replacements (dict[str, str]): The placeholder-to-original-value map.
    """

    chunks: list[str] = Field(min_length=1)
    replacements: dict[str, str] = Field(default_factory=dict)


@dataclass(frozen=True)
class PrivacyShieldContainer:
    """Group privacy-shield use cases.

    Attributes:
        anonymize_document (AnonymizeDocument): The anonymization use case.
    """

    anonymize_document: object


class FallbackPromptAnonymizer:
    """Provide a development fallback when the model cannot be loaded.

    Attributes:
        load_error (Exception): The error raised while loading the real model.
    """

    def __init__(self, load_error: Exception) -> None:
        """Initialize the fallback anonymizer.

        Args:
            load_error (Exception): The model loading error.
        """
        self._load_error = load_error

    def execute(self, text: str) -> tuple[str, dict[str, str]]:
        """Anonymize a small set of obvious prompt values.

        Args:
            text (str): The original prompt.

        Returns:
            tuple[str, dict[str, str]]: The anonymized prompt and replacements.
        """
        replacements: dict[str, str] = {
            "[PROMPT_1]": text,
        }
        anonymized_text = "[PROMPT_1]"
        return anonymized_text, replacements


_container: PrivacyShieldContainer | None = None
app = FastAPI(
    title="GuardianAI Privacy Shield",
    version="0.1.0",
    description="API del modulo privacy-shield.",
)


@app.on_event("startup")
def initialize_model() -> None:
    """Load the anonymization model when the API starts."""
    get_container()


@app.get("/health")
def healthcheck() -> dict[str, str]:
    """Return the API health status.

    Returns:
        dict[str, str]: A simple status payload.
    """
    return {"status": "ok"}


@app.post("/api/anonymize")
def anonymize_text_route(payload: AnonymizeRequest) -> dict[str, object]:
    """Anonymize a prompt and return the replacement map.

    Args:
        payload (AnonymizeRequest): The request sent by the orchestrator.

    Returns:
        dict[str, object]: The anonymized prompt and replacement map.

    Raises:
        HTTPException: If the anonymizer fails.
    """
    try:
        anonymized_prompt, replacements = _anonymize_prompt(payload.text)
    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error

    _save_anonymization_debug(
        chat_id=payload.chat_id,
        anonymized_prompt=anonymized_prompt,
        replacements=replacements,
    )
    return {
        "anonymized_text": anonymized_prompt,
        "replacements": dict(replacements),
    }


@app.post("/api/deanonymize/stream")
def deanonymize_stream_route(
    payload: DeanonymizeStreamRequest,
) -> StreamingResponse:
    """Restore anonymized assistant chunks and stream safe text.

    Args:
        payload (DeanonymizeStreamRequest): The chunks and replacement map.

    Returns:
        StreamingResponse: The NDJSON stream consumed by the orchestrator.
    """
    chunks = _deanonymize_chunks(
        chunks=payload.chunks,
        replacements=payload.replacements,
    )
    return _build_streaming_response(chunks)


def get_container() -> PrivacyShieldContainer:
    """Return the lazily initialized dependency container.

    Returns:
        PrivacyShieldContainer: The initialized dependency container.
    """
    global _container

    if _container is None:
        _container = build_container()

    return _container


def build_container() -> PrivacyShieldContainer:
    """Build the privacy-shield dependency graph.

    Returns:
        PrivacyShieldContainer: The configured use case container.
    """
    try:
        from application.usecases.document_anonymizer.anonymize_document import (
            AnonymizeDocument,
        )
        from infrastructure.adapters.anonymization.llm_anonymizer import (
            LlmAnonymizer,
        )
        from infrastructure.adapters.evaluation.qwen_evaluator import (
            QwenEvaluator,
        )
        from infrastructure.adapters.model_loader.unsloth_provider import (
            UnslothProvider,
        )

        unsloth_provider = UnslothProvider()
        model_anonymizer, tokenizer_anonymizer = unsloth_provider.load(
            model_id="unsloth/Qwen3.5-0.8B",
            name="anonymizer_model",
        )

        evaluator = QwenEvaluator(
            model=model_anonymizer,
            tokenizer=tokenizer_anonymizer,
        )
        anonymizer = LlmAnonymizer(
            model=model_anonymizer,
            tokenizer=tokenizer_anonymizer,
        )

        return PrivacyShieldContainer(
            anonymize_document=AnonymizeDocument(
                evaluator=evaluator,
                anonymizer=anonymizer,
            ),
        )
    except Exception as error:
        return PrivacyShieldContainer(
            anonymize_document=FallbackPromptAnonymizer(error),
        )


def _anonymize_prompt(text: str) -> tuple[str, Mapping[str, str]]:
    """Anonymize a prompt and normalize the use case output.

    Args:
        text (str): The original user prompt.

    Returns:
        tuple[str, Mapping[str, str]]: The anonymized prompt and replacements.
    """
    result = get_container().anonymize_document.execute(text)

    if isinstance(result, tuple):
        anonymized_text, replacements = result
        return anonymized_text, replacements

    return result, {}


def _deanonymize_chunks(
    chunks: list[str],
    replacements: Mapping[str, str],
) -> Iterator[str]:
    """Restore placeholders from assistant chunks.

    Args:
        chunks (list[str]): The anonymized assistant chunks.
        replacements (Mapping[str, str]): The placeholder-to-original-value map.

    Returns:
        Iterator[str]: Restored chunks safe for web-ui.
    """
    from domain.streaming_deanonymization import StreamingDeanonymizer

    deanonymizer = StreamingDeanonymizer(replacements=replacements, strict=False)
    for chunk in chunks:
        restored_chunk = deanonymizer.push(chunk)
        if restored_chunk:
            yield restored_chunk

    final_chunk = deanonymizer.flush()
    if final_chunk:
        yield final_chunk


def _save_anonymization_debug(
    chat_id: str,
    anonymized_prompt: str,
    replacements: Mapping[str, str],
) -> None:
    """Store the anonymized prompt generated for manual verification.

    Args:
        chat_id (str): The chat that produced the prompt.
        anonymized_prompt (str): The prompt after anonymization.
        replacements (Mapping[str, str]): The placeholder-to-original map.
    """
    ANONYMIZATION_DEBUG_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "chat_id": chat_id,
        "anonymized_prompt": anonymized_prompt,
        "replacement_keys": list(replacements.keys()),
        "replacement_count": len(replacements),
    }

    with ANONYMIZATION_DEBUG_PATH.open("a", encoding="utf-8") as debug_file:
        debug_file.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _build_streaming_response(chunks: Iterator[str]) -> StreamingResponse:
    """Serialize safe text chunks as NDJSON stream events.

    Args:
        chunks (Iterator[str]): The safe chunks to stream to web-ui.

    Returns:
        StreamingResponse: The NDJSON stream response.
    """
    def event_stream() -> Iterator[str]:
        """Yield safe stream events as JSON lines.

        Yields:
            str: One JSON line containing a stream event.
        """
        try:
            for chunk in chunks:
                yield json.dumps(
                    {
                        "event": "chunk",
                        "content": chunk,
                    },
                    ensure_ascii=True,
                ) + "\n"

            yield json.dumps(
                {
                    "event": "completed",
                },
                ensure_ascii=True,
            ) + "\n"
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


def main() -> None:
    """Run the privacy-shield API."""
    uvicorn.run(app, host="0.0.0.0", port=8002)


if __name__ == "__main__":
    main()
