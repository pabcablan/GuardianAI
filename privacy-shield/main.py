import json
import uvicorn
import asyncio
import httpx
import json
import uuid
import os
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

from infrastructure.adapters.evaluation.evaluator_provider import EvaluatorProvider
from infrastructure.adapters.anonymization.anonymizer_provider import AnonymizerProvider
from application.usecases.document_anonymizer.anonymize_document import AnonymizeDocument
from application.body_params_schemas.anonymize_request import AnonymizeRequest
from application.usecases.document_deanonymizer.deanonymize_document_stream import DeanonymizeDocumentStream
from infrastructure.adapters.deanonymization.streaming_deanonymizer import StreamingDeanonymizer
from application.body_params_schemas.deanonymize_request import DeanonymizeRequest
from application.usecases.document_anonymizer.anonymize_document_optimized import AnonymizeDocumentOptimized

async def main():
    app = FastAPI()
    anonymization_sessions: dict[str, dict[str, str]] = {}

    client = httpx.AsyncClient(timeout=None)

    MODEL_PROVIDER_URL = os.getenv("MODEL_PROVIDER_URL", "http://localhost:8006/generate_response")
    MODEL_NAME = os.getenv("PRIVACY_MODEL_NAME", "privacy_anonymizer")

    evaluator_provider = EvaluatorProvider(use_api=True, api_url=MODEL_PROVIDER_URL, client=client)
    evaluator = evaluator_provider.get_evaluator(model_alias=MODEL_NAME)

    provider_std = AnonymizerProvider(use_api=True, optimized=False, api_url=MODEL_PROVIDER_URL, client=client)
    anonymizer_std = provider_std.get_anonymizer(model_alias=MODEL_NAME)
    
    provider_opt = AnonymizerProvider(use_api=True, optimized=True, api_url=MODEL_PROVIDER_URL, client=client)
    anonymizer_opt = provider_opt.get_anonymizer(model_alias=MODEL_NAME)

    anonymize_usecase = AnonymizeDocument(evaluator=evaluator, anonymizer=anonymizer_std)
    anonymize_optimized_usecase = AnonymizeDocumentOptimized(anonymizer=anonymizer_opt)

    @app.post("/anonymize")
    async def anonymize_route(request: AnonymizeRequest):
        return await anonymize_usecase.execute(
            request.text,
            settings=request.settings,
        )
    
    @app.post("/anonymize/optimized")
    async def anonymize_optimized_route(request: AnonymizeRequest):
        return await anonymize_optimized_usecase.execute(
            request.text,
            settings=request.settings,
        )

    @app.post("/deanonymize/stream")
    async def deanonymize_route(request: DeanonymizeRequest):
        deanonymizer = StreamingDeanonymizer()
        use_case = DeanonymizeDocumentStream(deanonymizer)

        async def transform_to_json():
            async for restored_text in use_case.execute(request.chunks, request.replacements):
                yield json.dumps({"event": "chunk", "content": restored_text}, ensure_ascii=False) + "\n"
            yield json.dumps({"event": "completed"}) + "\n"

        return StreamingResponse( transform_to_json(),media_type="application/x-ndjson",
            headers={"X-Accel-Buffering": "no"})
    
    config = uvicorn.Config(app, host="0.0.0.0", port=8002)
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
