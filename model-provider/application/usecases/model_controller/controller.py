"""Application controller for model lifecycle and inference operations."""
from __future__ import annotations

from fastapi.concurrency import run_in_threadpool

from application.body_params_schemas.load_model_request import LoadModelRequest
from infrastructure.ports.model_repository import ModelRepository
from infrastructure.ports.text_generator import TextGenerator


class Controller:
    """Coordinate model loading, unloading, listing, and inference."""

    def __init__(
        self,
        model_loader: ModelRepository,
        inference_engine: TextGenerator,
    ) -> None:
        """Initialize the controller dependencies.

        Args:
            model_loader (ModelRepository): The model runtime repository.
            inference_engine (TextGenerator): The inference engine used to
                produce responses from loaded models.
        """
        self.model_loader = model_loader
        self.inference_engine = inference_engine

    async def load_model(self, request: LoadModelRequest) -> str:
        """Load one model using the provided runtime configuration.

        Args:
            request (LoadModelRequest): The model loading request.

        Returns:
            str: A human-readable status message.
        """
        try:
            await self.model_loader.load(
                request.model_id,
                request.name,
                **self._build_loader_kwargs(request),
            )
            return f"Model '{request.name}' loaded successfully."
        except Exception as error:
            return f"Error loading model: {error}"

    async def unload_model(self, name: str) -> str:
        """Unload one model from memory.

        Args:
            name (str): The loaded model name.

        Returns:
            str: A human-readable status message.
        """
        try:
            await self.model_loader.unload(name)
            return f"Model '{name}' unloaded successfully."
        except Exception as error:
            return f"Error unloading model: {error}"

    async def get_model_status(self, name: str) -> str:
        """Return whether one model is currently loaded.

        Args:
            name (str): The loaded model name.

        Returns:
            str: A human-readable status message.
        """
        try:
            await self.model_loader.get(name)
            return f"Model '{name}' is loaded."
        except Exception:
            return f"Model '{name}' is NOT loaded."

    async def list_all_models(self) -> list[dict[str, str]]:
        """Return the registry of loaded models.

        Returns:
            list[dict[str, str]]: Loaded model names and identifiers.
        """
        return await self.model_loader.list_loaded_models()

    async def generate_response(
        self,
        model_name: str,
        system_prompt: str | None,
        prompt: str,
        document_base64: str | None,
    ) -> str:
        """Generate one response from a loaded model.

        Args:
            model_name (str): The runtime name of the loaded model.
            system_prompt (str | None): Optional system instructions.
            prompt (str): The user prompt or extraction instruction.
            document_base64 (str | None): Optional PDF payload for
                document-aware inference.

        Returns:
            str: The generated model response or an error message.
        """
        try:
            model, processor = await self.model_loader.get(model_name)
            return await run_in_threadpool(
                self.inference_engine.generate,
                system_prompt,
                prompt,
                model,
                processor,
                document_base64,
            )
        except Exception as error:
            return f"Error generating response: {error}"

    def _build_loader_kwargs(
        self,
        request: LoadModelRequest,
    ) -> dict[str, object]:
        """Build loader-specific keyword arguments from one request.

        Args:
            request (LoadModelRequest): The model loading request.

        Returns:
            dict[str, object]: Loader-specific runtime options.
        """
        if request.model_id.startswith("unsloth/"):
            return request.unsloth.model_dump() if request.unsloth else {}

        return (
            request.transformers.model_dump()
            if request.transformers
            else {}
        )
