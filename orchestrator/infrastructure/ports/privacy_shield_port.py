"""Port for requesting anonymization services from privacy-shield."""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any


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


class PrivacyShieldPort(ABC):
    """Define how orchestrator consumes privacy-shield operations."""

    @abstractmethod
    async def anonymize(
        self,
        chat_id: str,
        text: str,
        settings: dict[str, str] | None = None,
    ) -> AnonymizedPrompt:
        """Anonymize text through privacy-shield.

        Args:
            chat_id (str): The chat that owns the prompt.
            text (str): The original prompt.
            settings (dict[str, str] | None): The selected anonymization
                categories from the UI.

        Returns:
            AnonymizedPrompt: The anonymized text and privacy-shield session.
        """
        ...

    @abstractmethod
    async def deanonymize_stream(
        self,
        chunks: AsyncIterator[str],
        replacements: dict[str, str],
    ) -> AsyncIterator[dict[str, Any]]:
        """Restore anonymized stream chunks through privacy-shield.

        Args:
            chunks (AsyncIterator[str]): The anonymized assistant response chunks.
            replacements (dict[str, str]): Placeholder replacement mappings.

        Returns:
            AsyncIterator[dict[str, Any]]: NDJSON-like stream events emitted by
                privacy-shield.
        """
        ...
