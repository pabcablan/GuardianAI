from infrastructure.ports.model_repository import ModelRepository
from infrastructure.ports.text_generator import TextGenerator
from application.body_params_schemas.load_model_request import LoadModelRequest


class Controller:
    def __init__(self, model_loader: ModelRepository, inference_engine: TextGenerator):
        self.model_loader = model_loader
        self.inference_engine = inference_engine

    def load_model(self, request: LoadModelRequest) -> str:
        try:
            if request.model_id.startswith("unsloth/"):
                kwargs = request.unsloth.model_dump() if request.unsloth else {}
            else:
                kwargs = request.transformers.model_dump() if request.transformers else {}

            self.model_loader.load(request.model_id, request.name, **kwargs)

            return f"Model '{request.name}' loaded successfully."

        except Exception as e:
            return f"Error loading model: {str(e)}"

    def unload_model(self, name: str) -> str:
        try:
            self.model_loader.unload(name)
            return f"Model '{name}' unloaded successfully."
        except Exception as e:
            return f"Error unloading model: {str(e)}"
    
    def get_model_status(self, name: str) -> str:
        try:
            self.model_loader.get(name)
            return f"Model '{name}' is loaded."
        except Exception:
            return f"Model '{name}' is NOT loaded."

    def list_all_models(self) -> list[dict[str, str]]:
        return self.model_loader.list_loaded_models()

    def generate_response(self, model_name: str, prompt: str, document_base64: str | None) -> str:
        try:
            model, tokenizer = self.model_loader.get(model_name)
            return self.inference_engine.generate(prompt, model, tokenizer, document_base64)
        except Exception as e:
            return f"Error generating response: {str(e)}"