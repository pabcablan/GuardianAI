"""Domain entity and business rules for chat conversations."""
from __future__ import annotations

from dataclasses import dataclass, field

from domain.message import Message


@dataclass
class Chat:
    """Represent a conversation managed by the web-ui module.

    Attributes:
        chat_id (str): The conversation identifier.
        title (str): The conversation title.
        messages (list[Message]): The ordered conversation messages.
    """

    chat_id: str
    title: str
    messages: list[Message] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate the required chat fields.

        Raises:
            ValueError: If the chat identifier or title is empty.
        """
        if not self.chat_id.strip():
            raise ValueError("Chat id cannot be empty.")
        if not self.title.strip():
            raise ValueError("Chat title cannot be empty.")

    def add_message(self, message: Message) -> None:
        """Add one message to the conversation history.

        Args:
            message (Message): The message to append.
        """
        self.messages.append(message)

    def rename(self, title: str) -> None:
        """Update the conversation title.

        Args:
            title (str): The new title to apply.

        Raises:
            ValueError: If the normalized title is empty.
        """
        normalized_title = title.strip()
        if not normalized_title:
            raise ValueError("Chat title cannot be empty.")
        self.title = normalized_title
