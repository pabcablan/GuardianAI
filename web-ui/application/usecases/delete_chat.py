from __future__ import annotations

from infrastructure.ports.internal.chat_repository_port import ChatRepositoryPort


class DeleteChatUseCase:
    def __init__(self, gateway: ChatRepositoryPort) -> None:
        self._gateway = gateway

    def execute(self, chat_id: str) -> None:
        if not chat_id.strip():
            raise ValueError("Chat id cannot be empty.")

        self._gateway.delete_chat(chat_id)
