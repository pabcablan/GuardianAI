from pydantic import BaseModel

class AnonymizeRequest(BaseModel):
    text: str
    settings: dict[str, str] | None = None
