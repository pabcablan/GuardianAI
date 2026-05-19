from abc import ABC, abstractmethod


class Anonymizer(ABC):
    """Contract for components that anonymize input text."""

    @abstractmethod
    async def anonymize(
        self,
        text: str,
        settings: dict[str, str] | None = None,
    ) -> dict[str, object]:
        """Return anonymized text plus the placeholder replacement map."""
        ...
