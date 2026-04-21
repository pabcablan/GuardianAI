from __future__ import annotations

from dataclasses import dataclass

from infrastructure.ports.internal.chat_repository_port import ChatRepositoryPort


@dataclass(frozen=True)
class CreateChatCommand:
    title: str | None = None


@dataclass(frozen=True)
class CreateChatResult:
    chat_id: str
    title: str

class CreateChatUseCase:
    def __init__(self, gateway: ChatRepositoryPort) -> None:
        self._gateway = gateway

    def execute(self, command: CreateChatCommand) -> CreateChatResult:
        title = (command.title or "Nuevo chat").strip() or "Nuevo chat"
        return self._gateway.create_chat(title)
