from abc import ABC, abstractmethod
from typing import Generator
from domain.value_objects.message import Message


class LanguageModel(ABC):

    @abstractmethod
    def stream(self, messages: list[Message], model: str) -> Generator[str, None, None]:
        ...