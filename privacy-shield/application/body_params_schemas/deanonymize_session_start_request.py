from pydantic import BaseModel


class DeanonymizeSessionStartRequest(BaseModel):
    """Request body used to open a deanonymization session."""

    session_id: str
    replacements: dict[str, str]
