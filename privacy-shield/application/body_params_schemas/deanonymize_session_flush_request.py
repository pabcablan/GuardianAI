from pydantic import BaseModel


class DeanonymizeSessionFlushRequest(BaseModel):
    """Request body used to flush one deanonymization session."""

    session_id: str
