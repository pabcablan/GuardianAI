"""FastAPI entrypoint for the GuardianAI model-provider service."""
from __future__ import annotations

import os
import traceback

import uvicorn
from fastapi import FastAPI, HTTPException, status

from application.body_params_schemas.generate_response_request import (
    GenerateRequest,
)
from application.body_params_schemas.load_model_request import LoadModelRequest
from application.usecases.model_controller.controller import Controller
from infrastructure.ports.model_repository import ModelRepository
from infrastructure.ports.text_generator import TextGenerator


DEFAULT_PRIVACY_MODEL_ID = os.getenv(
    "DEFAULT_PRIVACY_MODEL_ID",
    "unsloth/Qwen3.5-2B",
)
DEFAULT_PRIVACY_MODEL_NAME = os.getenv(
    "DEFAULT_PRIVACY_MODEL_NAME",
    "privacy_anonymizer",
)
DEFAULT_DOCUMENT_MODEL_ID = os.getenv(
    "DEFAULT_DOCUMENT_MODEL_ID",
    DEFAULT_PRIVACY_MODEL_ID,
)
DEFAULT_DOCUMENT_MODEL_NAME = os.getenv(
    "DEFAULT_DOCUMENT_MODEL_NAME",
    "document_extractor",
)


class LazyUnslothLoader(ModelRepository):
    """Import the Unsloth loader only when a model operation is requested."""

    def __init__(self) -> None:
        """Initialize the lazy loader."""
        self._loader = None

    def _get_loader(self):
        """Return the real Unsloth loader.

        Returns:
            UnslothLoader: The concrete Unsloth model loader.
        """
        if self._loader is None:
            from infrastructure.adapters.model_loader.unsloth_repository import (
                UnslothLoader,
            )

            self._loader = UnslothLoader()
        return self._loader

    def load(self, model_id: str, name: str, **kwargs):
        """Load a model through the concrete loader."""
        return self._get_loader().load(model_id, name, **kwargs)

    def get(self, name: str):
        """Get a loaded model through the concrete loader."""
        return self._get_loader().get(name)

    def unload(self, name: str):
        """Unload a model through the concrete loader."""
        return self._get_loader().unload(name)

    def list_loaded_models(self) -> list[dict[str, str]]:
        """List loaded models through the concrete loader."""
        return self._get_loader().list_loaded_models()


class LazyModelInferenceEngine(TextGenerator):
    """Import the inference engine only when generation is requested."""

    def __init__(self) -> None:
        """Initialize the lazy inference engine."""
        self._engine = None

    def _get_engine(self):
        """Return the concrete inference engine.

        Returns:
            ModelInferenceEngine: The concrete inference engine.
        """
        if self._engine is None:
            from infrastructure.adapters.inference.model_inference_engine import (
                ModelInferenceEngine,
            )

            self._engine = ModelInferenceEngine()
        return self._engine

    def generate(
        self,
        prompt: str,
        model,
        tokenizer,
        document_base64=None,
    ) -> str:
        """Generate text through the concrete inference engine."""
        return self._get_engine().generate(
            prompt=prompt,
            model=model,
            tokenizer=tokenizer,
            document_base64=document_base64,
        )


def _load_startup_model(
    controller: Controller,
    model_id: str,
    model_name: str,
    label: str,
) -> None:
    """Load one startup model through the controller.

    Args:
        controller (Controller): The model controller.
        model_id (str): The model identifier.
        model_name (str): The model registry name.
        label (str): A human-readable model role.

    Raises:
        RuntimeError: If the model cannot be loaded.
    """
    print(
        f"Loading default {label} model '{model_name}' from '{model_id}'...",
        flush=True,
    )
    request = LoadModelRequest(
        model_id=model_id,
        name=model_name,
    )
    result = controller.load_model(request)
    print(result, flush=True)
    if result.startswith("Error "):
        raise RuntimeError(result)


def build_app() -> FastAPI:
    """Build the model-provider API.

    Returns:
        FastAPI: The configured API application.
    """
    controller = Controller(
        model_loader=LazyUnslothLoader(),
        inference_engine=LazyModelInferenceEngine(),
    )
    app = FastAPI(
        title="GuardianAI Model Provider",
        version="0.1.0",
        description="Centralized model loading and inference API.",
    )

    @app.on_event("startup")
    def load_default_models() -> None:
        """Load default models when the service starts."""
        _load_startup_model(
            controller=controller,
            model_id=DEFAULT_PRIVACY_MODEL_ID,
            model_name=DEFAULT_PRIVACY_MODEL_NAME,
            label="privacy",
        )
        if (
            DEFAULT_DOCUMENT_MODEL_NAME != DEFAULT_PRIVACY_MODEL_NAME
            and DEFAULT_DOCUMENT_MODEL_ID != DEFAULT_PRIVACY_MODEL_ID
        ):
            _load_startup_model(
                controller=controller,
                model_id=DEFAULT_DOCUMENT_MODEL_ID,
                model_name=DEFAULT_DOCUMENT_MODEL_NAME,
                label="document",
            )

    @app.get("/health")
    def healthcheck() -> dict[str, str]:
        """Return the API health status.

        Returns:
            dict[str, str]: A simple health payload.
        """
        return {"status": "ok"}

    @app.post("/load_model/")
    def load_model(request: LoadModelRequest) -> str:
        """Load a model.

        Args:
            request (LoadModelRequest): The model loading request.

        Returns:
            str: The loading result.
        """
        result = controller.load_model(request)
        if result.startswith("Error "):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result,
            )
        return result

    @app.post("/unload_model/")
    def unload_model(name: str) -> str:
        """Unload a model.

        Args:
            name (str): The registered model name.

        Returns:
            str: The unload result.
        """
        return controller.unload_model(name)

    @app.get("/model_status/")
    def model_status(name: str) -> str:
        """Return model loading status.

        Args:
            name (str): The registered model name.

        Returns:
            str: The model status.
        """
        return controller.get_model_status(name)

    @app.get("/list_models/")
    def list_models() -> list[dict[str, str]]:
        """List loaded models.

        Returns:
            list[dict[str, str]]: Loaded models.
        """
        return controller.list_all_models()

    @app.post("/generate_response/")
    def generate_response(request: GenerateRequest) -> str:
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
            result = controller.generate_response(
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
