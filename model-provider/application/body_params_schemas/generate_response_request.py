from pydantic import BaseModel

class GenerateRequest(BaseModel):
    model_name: str
    system_prompt: str | None = None
    prompt: str
    document_base64: str | None = None