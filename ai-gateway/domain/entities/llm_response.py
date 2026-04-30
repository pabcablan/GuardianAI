from dataclasses import dataclass
from datetime import datetime


@dataclass
class LLMResponse:
    id: str
    request_id: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    finish_reason: str
    completed_at: datetime