from __future__ import annotations

from dataclasses import dataclass

from infrastructure.ports.internal.message_service_port import MessageServicePort


@dataclass(frozen=True)
class SendMessageCommand:
    chat_id: str
    content: str


@dataclass(frozen=True)
class SendMessageResult:
    user_message_id: str
    assistant_message_id: str | None
    assistant_content: str | None

class SendMessageUseCase:
    def __init__(self, gateway: MessageServicePort) -> None:
        self._gateway = gateway

    def execute(self, command: SendMessageCommand) -> SendMessageResult:
        content = command.content.strip()
        if not content:
            raise ValueError("Message content cannot be empty.")

        return self._gateway.send_message(command.chat_id, content)
