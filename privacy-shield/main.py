import json
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

import uvicorn
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from application.usecases.document_anonymizer.anonymize_document import (
    AnonymizeDocument,
)
from application.usecases.stream_safe_response import (
    StreamSafeResponseCommand,
    StreamSafeResponseUseCase,
)
from infrastructure.adapters.anonymization.llm_anonymizer import LlmAnonymizer
from infrastructure.adapters.evaluation.qwen_evaluator import QwenEvaluator
from infrastructure.adapters.fake_assistant_stream_gateway import (
    FakeAssistantStreamGateway,
)
from infrastructure.adapters.model_loader.unsloth_provider import (
    UnslothProvider,
)


ANONYMIZATION_DEBUG_PATH = (
    Path(__file__).resolve().parent / "storage" / "anonymization_debug.jsonl"
)


class AnonymizeRequest(BaseModel):
    """Represent the message request sent by web-ui.

    Attributes:
        chat_id (str): The chat that will display the streamed response.
        text (str): The original user prompt to protect before calling the
            assistant service.
    """

    chat_id: str = Field(min_length=1)
    text: str = Field(min_length=1)


def main():
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

    anonymize_usecase = AnonymizeDocument(
        evaluator=evaluator,
        anonymizer=anonymizer,
    )
    stream_usecase = StreamSafeResponseUseCase(FakeAssistantStreamGateway())

    app = FastAPI()

    @app.post("/anonymize")
    def anonymize_route(payload: AnonymizeRequest):
        """Anonymize a user prompt and return a safe response stream.

        Args:
            payload (AnonymizeRequest): The request sent by web-ui.

        Returns:
            StreamingResponse: The NDJSON stream consumed by web-ui.
        """
        try:
            anonymized_prompt, replacements = _anonymize_prompt(
                anonymize_usecase,
                payload.text,
            )
            _save_anonymization_debug(
                chat_id=payload.chat_id,
                anonymized_prompt=anonymized_prompt,
                replacements=replacements,
            )
        except RuntimeError as error:
            return _build_error_stream(str(error))

        chunks = stream_usecase.execute(
            StreamSafeResponseCommand(
                anonymized_prompt=anonymized_prompt,
                replacements=replacements,
                strict=False,
            )
        )
        return _build_streaming_response(chunks)

    uvicorn.run(app, host="0.0.0.0", port=7002)


def _anonymize_prompt(
    anonymize_usecase: AnonymizeDocument,
    text: str,
) -> tuple[str, Mapping[str, str]]:
    """Anonymize a prompt and normalize the use case output.

    Args:
        anonymize_usecase (AnonymizeDocument): The prompt anonymization use case.
        text (str): The original user prompt.

    Returns:
        tuple[str, Mapping[str, str]]: The anonymized prompt and replacements.
    """
    result = anonymize_usecase.execute(text)

    if isinstance(result, tuple):
        anonymized_text, replacements = result
        return anonymized_text, replacements

    return result, {}


def _save_anonymization_debug(
    chat_id: str,
    anonymized_prompt: str,
    replacements: Mapping[str, str],
) -> None:
    """Store the anonymized prompt generated for manual verification.

    The debug file avoids storing original prompts or original replacement
    values. It only stores the anonymized text and placeholder keys.

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


def _build_error_stream(detail: str) -> StreamingResponse:
    """Serialize one error as an NDJSON stream.

    Args:
        detail (str): The error detail.

    Returns:
        StreamingResponse: The NDJSON error stream response.
    """
    return _build_streaming_response(_error_chunk(detail))


def _error_chunk(detail: str) -> Iterator[str]:
    """Create a stream with one readable error chunk.

    Args:
        detail (str): The error detail.

    Returns:
        Iterator[str]: A one-item stream with the error detail.
    """
    yield f"Privacy-shield error: {detail}"


if __name__ == "__main__":
    main()
