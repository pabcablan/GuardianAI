import uvicorn
from fastapi import FastAPI

from infrastructure.adapters.model_loader.unsloth_repository import UnslothLoader
from infrastructure.adapters.inference.model_inference_engine import ModelInferenceEngine
from application.usecases.model_controller.controller import Controller
from application.body_params_schemas.load_model_request import LoadModelRequest
from application.body_params_schemas.generate_response_request import GenerateRequest

def main():
    unsloth_provider = UnslothLoader()
    inference_engine = ModelInferenceEngine()

    controller = Controller(unsloth_provider, inference_engine)

    app = FastAPI()

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
        print("SYSTEM PROMPT LEN:", len(request.system_prompt) if request.system_prompt else 0)
        
        if request.document_base64:
            print("DOCUMENT RECEIVED: YES")
        else:
            print("DOCUMENT RECEIVED: NO")

        
        return await controller.generate_response(request.model_name, request.system_prompt,
                                                   request.prompt, request.document_base64)
    
    uvicorn.run(app, host="0.0.0.0", port=7003)

if __name__ == "__main__":
    main()