"""In-memory registry for anonymization replacement mappings."""
from __future__ import annotations

from infrastructure.ports.privacy_shield_port import AnonymizedPrompt


class AnonymizationRegistry:
    """Store replacement mappings during an orchestrator process lifetime."""

    def __init__(self) -> None:
        """Initialize the in-memory registry."""
        self._replacements: dict[str, dict[str, str]] = {}
        self._chat_replacements: dict[str, dict[str, str]] = {}

    def store(
        self,
        anonymized_prompt: AnonymizedPrompt,
        chat_id: str | None = None,
    ) -> None:
        """Store replacements from an anonymized prompt.

        Args:
            anonymized_prompt (AnonymizedPrompt): The anonymization result.
            chat_id (str | None): The chat that owns the anonymization.
        """
        self._replacements[anonymized_prompt.anonymization_id] = dict(
            anonymized_prompt.replacements,
        )
        if chat_id is not None:
            chat_replacements = self._chat_replacements.setdefault(
                chat_id,
                {},
            )
            chat_replacements.update(anonymized_prompt.replacements)

    def get(self, anonymization_id: str) -> dict[str, str]:
        """Return replacements for an anonymization session.

        Args:
            anonymization_id (str): The anonymization session identifier.

        Returns:
            dict[str, str]: The replacement mappings.

        Raises:
            ValueError: If the anonymization session is unknown.
        """
        try:
            return self._replacements[anonymization_id]
        except KeyError as error:
            raise ValueError("Unknown anonymization id.") from error

    def get_for_chat(self, chat_id: str) -> dict[str, str]:
        """Return all replacements stored for a chat.

        Args:
            chat_id (str): The chat identifier.

        Returns:
            dict[str, str]: The accumulated replacement mappings.
        """
        return dict(self._chat_replacements.get(chat_id, {}))
