from pydantic import BaseModel


class DeanonymizeSessionChunkRequest(BaseModel):
    """Request body used to restore one streamed chunk."""

    session_id: str
    chunk: str
