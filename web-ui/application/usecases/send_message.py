"""Use case for sending messages to the assistant."""
from __future__ import annotations

from dataclasses import dataclass

from infrastructure.ports.internal.message_service_port import MessageServicePort


@dataclass(frozen=True)
class SendMessageCommand:
    """Represent the input required to send a message.

    Attributes:
        chat_id (str): The identifier of the target chat.
        content (str): The user message content.
    """

    chat_id: str
    content: str


@dataclass(frozen=True)
class SendMessageResult:
    """Represent the result returned after sending a message.

    Attributes:
        user_message_id (str): The generated user message identifier.
        assistant_message_id (str | None): The generated assistant message
            identifier, when a response is available.
        assistant_content (str | None): The assistant response content, when
            available.
    """

    user_message_id: str
    assistant_message_id: str | None
    assistant_content: str | None

class SendMessageUseCase:
    """Validate the user prompt and send it to the message service."""

    def __init__(self, gateway: MessageServicePort) -> None:
        """Initialize the use case.

        Args:
            gateway (MessageServicePort): The message service gateway.
        """
        self._gateway = gateway

    def execute(self, command: SendMessageCommand) -> SendMessageResult:
        """Send a normalized message and return the produced response.

        Args:
            command (SendMessageCommand): The message request data.

        Returns:
            SendMessageResult: The created message identifiers and response.

        Raises:
            ValueError: If the message content is empty.
        """
        content = command.content.strip()
        if not content:
            raise ValueError("Message content cannot be empty.")

        return self._gateway.send_message(command.chat_id, content)
