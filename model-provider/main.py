"""HTTP entrypoint for the model-provider service."""
from __future__ import annotations

import logging

import uvicorn
from fastapi import FastAPI

from application.body_params_schemas.generate_response_request import (
    GenerateRequest,
)
from application.body_params_schemas.load_model_request import LoadModelRequest
from application.usecases.model_controller.controller import Controller
from infrastructure.dependency_container import (
    build_controller,
    load_startup_models,
)


LOGGER = logging.getLogger(__name__)


def create_app(controller: Controller | None = None) -> FastAPI:
    """Create the FastAPI application for model-provider.

    Args:
        controller (Controller | None): Optional prebuilt controller for tests
            or alternative dependency wiring.

    Returns:
        FastAPI: The configured application instance.
    """
    resolved_controller = controller or build_controller()

    app = FastAPI(
        title="GuardianAI Model Provider",
        version="0.1.0",
        description="Loads local models and generates text responses.",
    )

    @app.on_event("startup")
    async def startup() -> None:
        """Load the default startup models."""
        await load_startup_models(resolved_controller)

    @app.post("/load_model")
    async def load_model(request: LoadModelRequest) -> str:
        """Load one model into the provider runtime.

        Args:
            request (LoadModelRequest): The model loading request.

        Returns:
            str: A human-readable status message.
        """
        return await resolved_controller.load_model(request)

    @app.post("/unload_model")
    async def unload_model(name: str) -> str:
        """Unload one model from memory.

        Args:
            name (str): The loaded model name.

        Returns:
            str: A human-readable status message.
        """
        return await resolved_controller.unload_model(name)

    @app.get("/model_status")
    async def model_status(name: str) -> str:
        """Return whether one model is currently loaded.

        Args:
            name (str): The loaded model name.

        Returns:
            str: A human-readable status message.
        """
        return await resolved_controller.get_model_status(name)

    @app.get("/list_models")
    async def list_models() -> list[dict[str, str]]:
        """Return the loaded model registry.

        Returns:
            list[dict[str, str]]: Loaded model names and identifiers.
        """
        return await resolved_controller.list_all_models()

    @app.post("/generate_response")
    async def generate_response(request: GenerateRequest) -> str:
        """Generate one response from a loaded model.

        Args:
            request (GenerateRequest): The inference request payload.

        Returns:
            str: The generated model response.
        """
        LOGGER.info(
            "MODEL_PROVIDER /generate_response model=%s prompt_len=%s "
            "system_prompt_len=%s document_received=%s",
            request.model_name,
            len(request.prompt),
            len(request.system_prompt) if request.system_prompt else 0,
            bool(request.document_base64),
        )
        return await resolved_controller.generate_response(
            request.model_name,
            request.system_prompt,
            request.prompt,
            request.document_base64,
        )

    return app


def main() -> None:
    """Run the model-provider development server."""
    uvicorn.run(create_app(), host="0.0.0.0", port=8010)


app = create_app()


if __name__ == "__main__":
    main()
