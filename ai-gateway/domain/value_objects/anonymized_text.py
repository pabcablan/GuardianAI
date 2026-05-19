"""Value object that wraps anonymized text exchanged with the provider."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AnonymizedText:
    """Represent non-empty anonymized text content."""

    value: str

    def __post_init__(self) -> None:
        """Validate that the wrapped text is not empty."""
        if not self.value or not self.value.strip():
            raise ValueError("AnonymizedText cannot be empty.")

    def __str__(self) -> str:
        """Return the wrapped text value."""
        return self.value
