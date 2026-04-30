"""Port for requesting anonymization services from privacy-shield."""
from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any, Mapping, Protocol


@dataclass(frozen=True)
class AnonymizedPrompt:
    """Represent a prompt anonymized by privacy-shield.

    Attributes:
        text (str): The anonymized prompt.
        replacements (Mapping[str, str]): The placeholder-to-original map.
    """

    text: str
    replacements: Mapping[str, str]


class PrivacyShieldPort(Protocol):
    """Define how orchestrator consumes privacy-shield operations."""

    def anonymize(self, chat_id: str, text: str) -> AnonymizedPrompt:
        """Anonymize text through privacy-shield.

        Args:
            chat_id (str): The chat that owns the prompt.
            text (str): The original prompt.

        Returns:
            AnonymizedPrompt: The anonymized text and replacement map.
        """

    def deanonymize_stream(
        self,
        chunks: list[str],
        replacements: Mapping[str, str],
    ) -> Iterator[dict[str, Any]]:
        """Stream deanonymized chunks through privacy-shield.

        Args:
            chunks (list[str]): The anonymized assistant response chunks.
            replacements (Mapping[str, str]): The placeholder-to-original map.

        Returns:
            Iterator[dict[str, Any]]: Safe stream events emitted by
            privacy-shield.
        """
