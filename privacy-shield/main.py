import asyncio
import os

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException

from application.body_params_schemas.anonymize_request import AnonymizeRequest
from application.body_params_schemas.deanonymize_session_chunk_request import (
    DeanonymizeSessionChunkRequest,
)
from application.body_params_schemas.deanonymize_session_flush_request import (
    DeanonymizeSessionFlushRequest,
)
from application.body_params_schemas.deanonymize_session_start_request import (
    DeanonymizeSessionStartRequest,
)
from application.services.deanonymization_session_registry import (
    DeanonymizationSessionRegistry,
)
from application.usecases.document_anonymizer.anonymize_document_optimized import (
    AnonymizeDocumentOptimized,
)
from application.usecases.document_deanonymizer.deanonymize_session_chunk import (
    DeanonymizeSessionChunk,
)
from application.usecases.document_deanonymizer.flush_deanonymize_session import (
    FlushDeanonymizeSession,
)
from application.usecases.document_deanonymizer.start_deanonymize_session import (
    StartDeanonymizeSession,
)
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
    deanonymization_session_ttl_seconds = float(
        os.getenv("DEANONYMIZATION_SESSION_TTL_SECONDS", "900")
    )

    provider = AnonymizerProvider(
        api_url=model_provider_url,
        client=client,
    )
    anonymizer = provider.get_anonymizer(model_alias=model_name)
    deanonymization_sessions = DeanonymizationSessionRegistry(
        session_ttl_seconds=deanonymization_session_ttl_seconds,
    )

    anonymize_usecase = AnonymizeDocumentOptimized(anonymizer=anonymizer)
    start_deanonymize_session_usecase = StartDeanonymizeSession(
        registry=deanonymization_sessions,
        deanonymizer_factory=StreamingDeanonymizer,
    )
    deanonymize_session_chunk_usecase = DeanonymizeSessionChunk(
        registry=deanonymization_sessions,
    )
    flush_deanonymize_session_usecase = FlushDeanonymizeSession(
        registry=deanonymization_sessions,
    )

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

    @app.post("/deanonymize/session/start")
    async def start_deanonymize_session_route(
        request: DeanonymizeSessionStartRequest,
    ):
        """Open a stateful deanonymization session.

        Args:
            request (DeanonymizeSessionStartRequest): Session identifier and
                replacement mappings.

        Returns:
            dict: Confirmation payload with the opened session identifier.
        """
        try:
            return start_deanonymize_session_usecase.execute(
                session_id=request.session_id,
                replacements=request.replacements,
            )
        except ValueError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error

    @app.post("/deanonymize/session/chunk")
    async def deanonymize_session_chunk_route(
        request: DeanonymizeSessionChunkRequest,
    ):
        """Restore one chunk within an active deanonymization session.

        Args:
            request (DeanonymizeSessionChunkRequest): Session identifier and
                one anonymized chunk.

        Returns:
            dict: The restored chunk content.
        """
        try:
            return deanonymize_session_chunk_usecase.execute(
                session_id=request.session_id,
                chunk=request.chunk,
            )
        except KeyError as error:
            raise HTTPException(status_code=404, detail="Unknown session.") from error

    @app.post("/deanonymize/session/flush")
    async def deanonymize_session_flush_route(
        request: DeanonymizeSessionFlushRequest,
    ):
        """Flush and close one active deanonymization session.

        Args:
            request (DeanonymizeSessionFlushRequest): Session identifier to
                close.

        Returns:
            dict: Any trailing restored buffered content.
        """
        try:
            return flush_deanonymize_session_usecase.execute(
                request.session_id,
            )
        except KeyError as error:
            raise HTTPException(status_code=404, detail="Unknown session.") from error

    config = uvicorn.Config(app, host="0.0.0.0", port=8002)
    server = uvicorn.Server(config)
    try:
        await server.serve()
    finally:
        await client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
