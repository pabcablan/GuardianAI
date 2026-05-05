import uvicorn
import asyncio
import httpx
from fastapi import FastAPI

from infrastructure.adapters.evaluation.evaluator_provider import EvaluatorProvider
from infrastructure.adapters.anonymization.anonymizer_provider import AnonymizerProvider
from application.usecases.document_anonymizer.anonymize_document import AnonymizeDocument
from application.body_params_schemas.anonymize_request import AnonymizeRequest

async def main():
    app = FastAPI()

    client = httpx.AsyncClient(timeout=None)

    MODEL_PROVIDER_URL = "https://localhost:7003/generate_response"
    MODEL_NAME = "anonymizer_model"

    evaluator_provider = EvaluatorProvider(use_api=True, api_url=MODEL_PROVIDER_URL, client=client)
    evaluator = evaluator_provider.get_evaluator(model_alias=MODEL_NAME)

    anonymizer_provider = AnonymizerProvider(use_api=True, api_url=MODEL_PROVIDER_URL, client=client)
    anonymizer = anonymizer_provider.get_anonymizer(model_alias=MODEL_NAME)

    anonymize_usecase = AnonymizeDocument(evaluator=evaluator, anonymizer=anonymizer)
    
    @app.post("/anonymize")
    async def anonymize_route(request: AnonymizeRequest):
        return await anonymize_usecase.execute(request.text)

    config = uvicorn.Config(app, host="0.0.0.0", port=7002)
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())