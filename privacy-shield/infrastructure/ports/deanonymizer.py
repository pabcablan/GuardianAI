from abc import ABC, abstractmethod


class Deanonymizer(ABC):
    """Contract for components that restore placeholders to original text."""

    @abstractmethod
    def deanonymize(self, text: str, replacements: dict[str, str]) -> str:
        """Restore placeholders from a streamed text fragment."""
        ...

    @abstractmethod
    def flush(self, replacements: dict[str, str]) -> str:
        """Return any buffered restored content once the stream ends."""
        ...
