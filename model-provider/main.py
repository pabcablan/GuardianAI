import uvicorn
from fastapi import FastAPI, HTTPException, status

from application.body_params_schemas.generate_response_request import (
    GenerateRequest,
)
from application.body_params_schemas.load_model_request import LoadModelRequest
from infrastructure.dependency_container import (
    build_controller,
    load_startup_models,
)


def build_app() -> FastAPI:
    """Build the model-provider API.

    Returns:
        FastAPI: The configured API application.
    """
    controller = build_controller()
    app = FastAPI(
        title="GuardianAI Model Provider",
        version="0.1.0",
        description="Centralized model loading and inference API.",
    )

    @app.on_event("startup")
    async def load_default_models() -> None:
        """Load default models when the service starts."""
        await load_startup_models(controller)

    @app.get("/health")
    async def healthcheck() -> dict[str, str]:
        """Return the API health status.

        Returns:
            dict[str, str]: A simple health payload.
        """
        return {"status": "ok"}

    @app.post("/load_model")
    async def load_model(request: LoadModelRequest):
        return await controller.load_model(request)

    @app.post("/unload_model")
    async def unload_model(name: str):
        return await controller.unload_model(name)
    
    @app.get("/model_status")
    async def model_status(name: str):
        return await controller.get_model_status(name)
    
    @app.get("/list_models")
    async def list_models():
        return await controller.list_all_models()
    
    @app.post("/generate_response")
    async def generate_response(request: GenerateRequest):
        print("MODEL:", request.model_name)
        print("PROMPT LEN:", len(request.prompt))
        
        if request.document_base64:
            print("DOCUMENT RECEIVED: YES")
        else:
            print("DOCUMENT RECEIVED: NO")

        
        return await controller.generate_response(request.model_name, request.prompt, request.document_base64)
    
    uvicorn.run(app, host="0.0.0.0", port=7003)

if __name__ == "__main__":
    main()
