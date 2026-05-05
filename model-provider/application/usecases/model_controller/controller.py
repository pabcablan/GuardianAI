"""Application controller for model loading and inference."""
from __future__ import annotations

from fastapi.concurrency import run_in_threadpool

from application.body_params_schemas.load_model_request import LoadModelRequest
from infrastructure.ports.model_repository import ModelRepository
from infrastructure.ports.text_generator import TextGenerator


class Controller:
    """Coordinate model repository and inference engine use cases."""

    def __init__(
        self,
        model_loader: ModelRepository,
        inference_engine: TextGenerator,
    ) -> None:
        """Initialize the controller.

        Args:
            model_loader (ModelRepository): Model loading adapter.
            inference_engine (TextGenerator): Text generation adapter.
        """
        self.model_loader = model_loader
        self.inference_engine = inference_engine

    async def load_model(self, request: LoadModelRequest) -> str:
        """Load a model without blocking the FastAPI event loop.

        Args:
            request (LoadModelRequest): The model loading request.

        Returns:
            str: The loading result message.
        """
        try:
            kwargs = self._build_loading_kwargs(request)
            await run_in_threadpool(
                self.model_loader.load,
                request.model_id,
                request.name,
                **kwargs,
            )
            return f"Model '{request.name}' loaded successfully."
        except Exception as error:
            return f"Error loading model: {error}"

    async def unload_model(self, name: str) -> str:
        """Unload a model without blocking the FastAPI event loop.

        Args:
            name (str): The model registry name.

        Returns:
            str: The unload result message.
        """
        try:
            await run_in_threadpool(self.model_loader.unload, name)
            return f"Model '{name}' unloaded successfully."
        except Exception as error:
            return f"Error unloading model: {error}"

    async def get_model_status(self, name: str) -> str:
        """Return whether a model is currently loaded.

        Args:
            name (str): The model registry name.

        Returns:
            str: The model status message.
        """
        try:
            await run_in_threadpool(self.model_loader.get, name)
            return f"Model '{name}' is loaded."
        except Exception:
            return f"Model '{name}' is NOT loaded."

    async def list_all_models(self) -> list[dict[str, str]]:
        """List all loaded models.

        Returns:
            list[dict[str, str]]: Loaded model metadata.
        """
        return await run_in_threadpool(self.model_loader.list_loaded_models)

    async def generate_response(
        self,
        model_name: str,
        prompt: str,
        document_base64: str | None,
    ) -> str:
        """Generate a model response without blocking the event loop.

        Args:
            model_name (str): The model registry name.
            prompt (str): The prompt to send to the model.
            document_base64 (str | None): Optional base64 document payload.

        Returns:
            str: The generated response, or an error message.
        """
        try:
            model, tokenizer = await run_in_threadpool(
                self.model_loader.get,
                model_name,
            )
            return await run_in_threadpool(
                self.inference_engine.generate,
                prompt,
                model,
                tokenizer,
                document_base64,
            )
        except Exception as error:
            return f"Error generating response: {error}"

    def _build_loading_kwargs(
        self,
        request: LoadModelRequest,
    ) -> dict:
        """Build loader options from a loading request.

        Args:
            request (LoadModelRequest): The loading request.

        Returns:
            dict: Options passed to the selected model loader.
        """
        if request.model_id.startswith("unsloth/"):
            return request.unsloth.model_dump() if request.unsloth else {}

        return request.transformers.model_dump() if request.transformers else {}
