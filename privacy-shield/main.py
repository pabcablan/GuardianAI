import uvicorn
import asyncio
import httpx
import json
import uuid
import os
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from infrastructure.adapters.evaluation.evaluator_provider import EvaluatorProvider
from infrastructure.adapters.anonymization.anonymizer_provider import AnonymizerProvider
from application.usecases.document_anonymizer.anonymize_document import AnonymizeDocument
from application.body_params_schemas.anonymize_request import AnonymizeRequest
from domain.streaming_deanonymization import StreamingDeanonymizer


class DeanonymizeStreamRequest(BaseModel):
    chunks: list[str] = Field(default_factory=list)
    anonymization_id: str | None = None
    replacements: dict[str, str] = Field(default_factory=dict)
    strict: bool = True

async def main():
    app = FastAPI()
    anonymization_sessions: dict[str, dict[str, str]] = {}

    client = httpx.AsyncClient(timeout=None)

    MODEL_PROVIDER_URL = os.getenv("MODEL_PROVIDER_URL", "http://localhost:8006/generate_response")
    MODEL_NAME = os.getenv("PRIVACY_MODEL_NAME", "privacy_anonymizer")

    evaluator_provider = EvaluatorProvider(use_api=True, api_url=MODEL_PROVIDER_URL, client=client)
    evaluator = evaluator_provider.get_evaluator(model_alias=MODEL_NAME)

    anonymizer_provider = AnonymizerProvider(use_api=True, api_url=MODEL_PROVIDER_URL, client=client)
    anonymizer = anonymizer_provider.get_anonymizer(model_alias=MODEL_NAME)

    anonymize_usecase = AnonymizeDocument(evaluator=evaluator, anonymizer=anonymizer)
    
    @app.post("/anonymize")
    async def anonymize_route(request: AnonymizeRequest):
        anonymized_text = await anonymize_usecase.execute(request.text)
        replacements = getattr(anonymizer, "last_replacements", {})
        anonymization_id = str(uuid.uuid4())
        anonymization_sessions[anonymization_id] = dict(replacements)
        return {
            "anonymized_text": anonymized_text,
            "anonymization_id": anonymization_id,
            "replacement_count": len(replacements),
        }

    @app.post("/deanonymize/stream")
    async def deanonymize_stream_route(request: DeanonymizeStreamRequest):
        replacements = request.replacements
        if request.anonymization_id:
            replacements = anonymization_sessions.get(
                request.anonymization_id,
                {},
            )

        deanonymizer = StreamingDeanonymizer(
            replacements=replacements,
            strict=request.strict,
        )

        def event_stream():
            try:
                for chunk in request.chunks:
                    restored_chunk = deanonymizer.push(chunk)
                    if restored_chunk:
                        yield json.dumps(
                            {
                                "event": "chunk",
                                "content": restored_chunk,
                            },
                            ensure_ascii=True,
                        ) + "\n"

                final_chunk = deanonymizer.flush()
                if final_chunk:
                    yield json.dumps(
                        {
                            "event": "chunk",
                            "content": final_chunk,
                        },
                        ensure_ascii=True,
                    ) + "\n"

                yield json.dumps({"event": "completed"}) + "\n"
            except ValueError as error:
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

    config = uvicorn.Config(app, host="0.0.0.0", port=8002)
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
