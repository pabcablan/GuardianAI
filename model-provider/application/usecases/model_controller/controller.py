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
        try:
            if request.model_id.startswith("unsloth/"):
                kwargs = request.unsloth.model_dump() if request.unsloth else {}
            else:
                kwargs = request.transformers.model_dump() if request.transformers else {}

            await self.model_loader.load(
                request.model_id,
                request.name,
                **kwargs,
            )

            return f"Model '{request.name}' loaded successfully."
        except Exception as error:
            return f"Error loading model: {error}"

      
    async def unload_model(self, name: str) -> str:
        """Unload a model without blocking the FastAPI event loop."""
        try:
            await self.model_loader.unload(name)
            return f"Model '{name}' unloaded successfully."
        except Exception as e:
            return f"Error unloading model: {str(e)}"
    
    async def get_model_status(self, name: str) -> str:
        try:
            await self.model_loader.get(name)
            return f"Model '{name}' is loaded."
        except Exception:
            return f"Model '{name}' is NOT loaded."

    async def list_all_models(self) -> list[dict[str, str]]:
        return await self.model_loader.list_loaded_models()

    async def generate_response(self, model_name: str, prompt: str, document_base64: str | None) -> str:
        try:
            model, tokenizer = await self.model_loader.get(model_name)
            return await run_in_threadpool(
                self.inference_engine.generate,
                prompt,
                model,
                tokenizer,
                document_base64,
            )
        except Exception as e:
            return f"Error generating response: {str(e)}"
