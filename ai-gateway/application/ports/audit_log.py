from abc import ABC, abstractmethod
from domain.entities.llm_request import LLMRequest
from domain.entities.llm_response import LLMResponse


class AuditLog(ABC):

    @abstractmethod
    async def log(self, request: LLMRequest, response: LLMResponse) -> None:
        ...