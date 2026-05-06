from abc import ABC, abstractmethod

class Deanonymizer(ABC):
    @abstractmethod
    def deanonymize(self, text: str, replacements: dict[str, str]) -> str:
        pass

    @abstractmethod
    def flush(self, replacements: dict[str, str]) -> str:
        pass