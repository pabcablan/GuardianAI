"""Port for requesting anonymization services from privacy-shield."""
from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class AnonymizedPrompt:
    """Represent a prompt anonymized by privacy-shield.

    Attributes:
        text (str): The anonymized prompt.
        replacements (dict[str, str]): The replacement mappings used to
            deanonymize later.
        anonymization_id (str): The privacy-shield session identifier.
        replacement_count (int): The number of stored replacements.
    """

    text: str
    replacements: dict[str, str]
    anonymization_id: str
    replacement_count: int = 0


class PrivacyShieldPort(Protocol):
    """Define how orchestrator consumes privacy-shield operations."""

    def anonymize(self, chat_id: str, text: str) -> AnonymizedPrompt:
        """Anonymize text through privacy-shield.

        Args:
            chat_id (str): The chat that owns the prompt.
            text (str): The original prompt.

        Returns:
            AnonymizedPrompt: The anonymized text and privacy-shield session.
        """

    def deanonymize_stream(
        self,
        chunks: list[str],
        replacements: dict[str, str],
    ) -> Iterator[dict[str, Any]]:
        """Stream deanonymized chunks through privacy-shield.

        Args:
            chunks (list[str]): The anonymized assistant response chunks.
            replacements (dict[str, str]): The replacements for deanonymization.

        Returns:
            Iterator[dict[str, Any]]: Safe stream events emitted by
            privacy-shield.
        """
