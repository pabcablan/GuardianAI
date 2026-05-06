from pydantic import BaseModel

class DeanonymizeRequest(BaseModel):
    chunks: list[str]
    replacements: dict[str, str]