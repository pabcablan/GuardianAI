import asyncio
import json
import os

import httpx
import uvicorn
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

from application.body_params_schemas.anonymize_request import AnonymizeRequest
from application.body_params_schemas.deanonymize_request import DeanonymizeRequest
from application.usecases.document_anonymizer.anonymize_document_optimized import (
    AnonymizeDocumentOptimized,
)
from application.usecases.document_deanonymizer.deanonymize_document_stream import DeanonymizeDocumentStream
from infrastructure.adapters.anonymization.anonymizer_provider import (
    AnonymizerProvider,
)
from infrastructure.adapters.deanonymization.streaming_deanonymizer import (
    StreamingDeanonymizer,
)


async def main() -> None:
    """Start the privacy-shield API service.

    Returns:
        None: Runs the FastAPI application until shutdown.
    """
    app = FastAPI()
    client = httpx.AsyncClient(timeout=None)

    model_provider_url = os.getenv(
        "MODEL_PROVIDER_URL",
        "http://localhost:8010/generate_response",
    )
    model_name = os.getenv("PRIVACY_MODEL_NAME", "qwen3.5")

    provider = AnonymizerProvider(
        api_url=model_provider_url,
        client=client,
    )
    anonymizer = provider.get_anonymizer(model_alias=model_name)

    anonymize_usecase = AnonymizeDocumentOptimized(anonymizer=anonymizer)

    @app.post("/anonymize/optimized")
    async def anonymize_optimized_route(request: AnonymizeRequest):
        """Anonymize input text using the optimized single-pass flow.

        Args:
            request (AnonymizeRequest): Input text plus anonymization settings.

        Returns:
            dict: Anonymized text and placeholder replacement mapping.
        """
        return await anonymize_usecase.execute(
            request.text,
            settings=request.settings,
        )

    @app.post("/deanonymize/stream")
    async def deanonymize_route(request: DeanonymizeRequest):
        """Restore placeholders from a streamed assistant response.

        Args:
            request (DeanonymizeRequest): Stream chunks and replacement mapping.

        Returns:
            StreamingResponse: NDJSON stream with restored text chunks.
        """
        deanonymizer = StreamingDeanonymizer()
        use_case = DeanonymizeDocumentStream(deanonymizer=deanonymizer)

        async def transform_to_json():
            """Emit restored chunks as NDJSON events.

            Yields:
                str: Serialized NDJSON events for chunk and completion updates.
            """
            async for restored_text in use_case.execute(
                request.chunks,
                request.replacements,
            ):
                yield (
                    json.dumps(
                        {"event": "chunk", "content": restored_text},
                        ensure_ascii=False,
                    )
                    + "\n"
                )
            yield json.dumps({"event": "completed"}) + "\n"

        return StreamingResponse(
            transform_to_json(),
            media_type="application/x-ndjson",
            headers={"X-Accel-Buffering": "no"},
        )

    config = uvicorn.Config(app, host="0.0.0.0", port=8002)
    server = uvicorn.Server(config)
    try:
        await server.serve()
    finally:
        await client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
