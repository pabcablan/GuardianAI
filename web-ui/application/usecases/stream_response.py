from __future__ import annotations

from dataclasses import dataclass

from infrastructure.ports.internal.stream_service_port import StreamServicePort


@dataclass(frozen=True)
class StreamResponseCommand:
    chat_id: str

class StreamResponseUseCase:
    def __init__(self, gateway: StreamServicePort) -> None:
        self._gateway = gateway

    def execute(self, command: StreamResponseCommand) -> list[str]:
        if not command.chat_id.strip():
            raise ValueError("Chat id cannot be empty.")

        return self._gateway.stream_response(command.chat_id)
