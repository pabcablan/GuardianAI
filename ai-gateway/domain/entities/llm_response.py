"""Domain entity that records one provider response summary."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class LLMResponse:
    """Represent one response returned by the upstream provider.

    Attributes:
        id (str): The response identifier.
        request_id (str): The originating request identifier.
        model (str): The provider model identifier.
        prompt_tokens (int): The prompt token count, when available.
        completion_tokens (int): The completion token count, when available.
        finish_reason (str): The provider finish reason.
        completed_at (datetime): The response completion timestamp.
    """

    id: str
    request_id: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    finish_reason: str
    completed_at: datetime
