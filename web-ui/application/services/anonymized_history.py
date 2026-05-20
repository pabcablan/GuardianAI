"""Build anonymized chat history to send to orchestrator."""
from __future__ import annotations

from infrastructure.ports.chat_repository_port import ChatRepositoryPort
from infrastructure.ports.orchestrator_response_types import (
    OrchestratorChatHistoryMessage,
)


class AnonymizedHistoryBuilder:
    """Build chat history containing only anonymized content."""

    def __init__(self, chat_repository: ChatRepositoryPort) -> None:
        self._chat_repository = chat_repository

    def build(
        self,
        chat_id: str,
        exclude_last_content: str | None = None,
    ) -> list[OrchestratorChatHistoryMessage]:
        """Build anonymized history for one chat.

        Args:
            chat_id (str): The chat whose messages should be inspected.
            exclude_last_content (str | None): Optional anonymized content to
                exclude from the end of the history.

        Returns:
            list[OrchestratorChatHistoryMessage]: The safe history.

        Raises:
            KeyError: If the chat does not exist.
        """
        chat = self._chat_repository.load_chat(chat_id)
        if chat is None:
            raise KeyError(chat_id)

        messages = [
            message
            for message in chat.messages
            if message.anonymized_content and message.anonymized_content.strip()
        ]
        if (
            exclude_last_content is not None
            and messages
            and messages[-1].anonymized_content == exclude_last_content
        ):
            messages = messages[:-1]

        return [
            OrchestratorChatHistoryMessage(
                role=message.role,
                content=message.anonymized_content or "",
            )
            for message in messages
        ]

    def build_replacements(self, chat_id: str) -> dict[str, str]:
        """Return the stored anonymization replacements for one chat.

        Args:
            chat_id (str): The chat whose replacements should be loaded.

        Returns:
            dict[str, str]: The accumulated placeholder replacement mappings.

        Raises:
            KeyError: If the chat does not exist.
        """
        chat = self._chat_repository.load_chat(chat_id)
        if chat is None:
            raise KeyError(chat_id)

        return self._chat_repository.get_chat_replacements(chat_id)
