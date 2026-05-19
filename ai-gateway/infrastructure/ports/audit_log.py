"""Port for persisting audited LLM request/response activity."""
from __future__ import annotations

from abc import ABC, abstractmethod

from domain.entities.llm_request import LLMRequest
from domain.entities.llm_response import LLMResponse


class AuditLog(ABC):
    """Define how ai-gateway persists audit trail entries."""

    @abstractmethod
    async def log(self, request: LLMRequest, response: LLMResponse) -> None:
        """Persist one audited request/response pair.

        Args:
            request (LLMRequest): The completed LLM request metadata.
            response (LLMResponse): The generated LLM response metadata.
        """
        ...
