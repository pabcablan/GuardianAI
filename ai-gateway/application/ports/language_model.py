from abc import ABC, abstractmethod
from typing import AsyncGenerator
from domain.value_objects.message import Message


class LanguageModel(ABC):

    @abstractmethod
    def stream(self, messages: list[Message], model: str) -> AsyncGenerator[str, None]:
        ...