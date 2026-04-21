from __future__ import annotations

from dataclasses import dataclass

from infrastructure.ports.internal.chat_repository_port import ChatRepositoryPort


@dataclass(frozen=True)
class ChatSummary:
    chat_id: str
    title: str
    last_message_preview: str
    updated_at: str

class ListChatsUseCase:
    def __init__(self, gateway: ChatRepositoryPort) -> None:
        self._gateway = gateway

    def execute(self) -> list[ChatSummary]:
        return self._gateway.list_chats()
