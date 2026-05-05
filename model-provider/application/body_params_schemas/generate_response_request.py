from pydantic import BaseModel

class GenerateRequest(BaseModel):
    model_name: str
    prompt: str
    document_base64: str | None = None