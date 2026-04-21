from __future__ import annotations

from dataclasses import dataclass

from infrastructure.ports.internal.chat_repository_port import ChatRepositoryPort


@dataclass(frozen=True)
class RenameChatCommand:
    chat_id: str
    title: str

class RenameChatUseCase:
    def __init__(self, gateway: ChatRepositoryPort) -> None:
        self._gateway = gateway

    def execute(self, command: RenameChatCommand) -> None:
        title = command.title.strip()
        if not command.chat_id.strip():
            raise ValueError("Chat id cannot be empty.")
        if not title:
            raise ValueError("Chat title cannot be empty.")

        self._gateway.rename_chat(command.chat_id, title)
