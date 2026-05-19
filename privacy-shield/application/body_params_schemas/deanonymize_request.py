from pydantic import BaseModel


class DeanonymizeRequest(BaseModel):
    """Request body for streamed deanonymization."""

    chunks: list[str]
    replacements: dict[str, str]
