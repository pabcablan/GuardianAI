from pydantic import BaseModel


class AnonymizeRequest(BaseModel):
    """Request body for document anonymization."""

    text: str
    settings: dict[str, str] | None = None
