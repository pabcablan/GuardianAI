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

    def add_messages(self, messages: list[Message]) -> None:
        """Add several messages to the conversation history.

        Args:
            messages (list[Message]): The messages to append in order.
        """
        self.messages.extend(messages)

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

    def last_message_preview(self) -> str:
        """Return the latest message content as a preview.

        Returns:
            str: The latest message content, or an empty string when there are
            no messages.
        """
        if not self.messages:
            return ""
        return self.messages[-1].content

    def updated_at(self) -> str:
        """Return the timestamp used to display the chat update time.

        Returns:
            str: The latest message timestamp, or the default value for empty
            conversations.
        """
        if not self.messages:
            return "Ahora"
        return self.messages[-1].created_at

    def last_assistant_chunks(self) -> list[str]:
        """Split the latest assistant response into simple chunks.

        Returns:
            list[str]: The latest assistant response split by whitespace.
        """
        for message in reversed(self.messages):
            if message.role == "assistant":
                return message.content.split()
        return []
