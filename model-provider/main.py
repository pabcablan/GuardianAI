"""FastAPI entrypoint for the GuardianAI model-provider service."""
from __future__ import annotations

import traceback

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

    @app.post("/load_model/")
    async def load_model(request: LoadModelRequest) -> str:
        """Load a model.

        Args:
            request (LoadModelRequest): The model loading request.

        Returns:
            str: The loading result.
        """
        result = await controller.load_model(request)
        if result.startswith("Error "):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result,
            )
        return result

    @app.post("/unload_model/")
    async def unload_model(name: str) -> str:
        """Unload a model.

        Args:
            name (str): The registered model name.

        Returns:
            str: The unload result.
        """
        result = await controller.unload_model(name)
        if result.startswith("Error "):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result,
            )
        return result

    @app.get("/model_status/")
    async def model_status(name: str) -> str:
        """Return model loading status.

        Args:
            name (str): The registered model name.

        Returns:
            str: The model status.
        """
        return await controller.get_model_status(name)

    @app.get("/list_models/")
    async def list_models() -> list[dict[str, str]]:
        """List loaded models.

        Returns:
            list[dict[str, str]]: Loaded models.
        """
        return await controller.list_all_models()

    @app.post("/generate_response/")
    async def generate_response(request: GenerateRequest) -> str:
        """Generate text with a loaded model.

        Args:
            request (GenerateRequest): The inference request.

        Returns:
            str: The generated text.
        """
        print(
            "MODEL-PROVIDER /generate_response "
            f"model={request.model_name} "
            f"prompt_len={len(request.prompt)} "
            f"has_document={request.document_base64 is not None}",
            flush=True,
        )
        try:
            result = await controller.generate_response(
                model_name=request.model_name,
                prompt=request.prompt,
                document_base64=request.document_base64,
            )
        except Exception as error:
            traceback.print_exc()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{type(error).__name__}: {error}",
            ) from error

        if result.startswith("Error "):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result,
            )
        return result

    return app


app = build_app()


def main() -> None:
    """Run the model-provider API."""
    uvicorn.run(app, host="0.0.0.0", port=8006)


if __name__ == "__main__":
    main()
