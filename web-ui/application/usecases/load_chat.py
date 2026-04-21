from __future__ import annotations

from domain.chat import Chat as ChatDetail
from infrastructure.ports.internal.chat_repository_port import ChatRepositoryPort


class LoadChatUseCase:
    def __init__(self, gateway: ChatRepositoryPort) -> None:
        self._gateway = gateway

    def execute(self, chat_id: str) -> ChatDetail | None:
        return self._gateway.load_chat(chat_id)
