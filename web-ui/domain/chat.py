from __future__ import annotations

from dataclasses import dataclass, field

from domain.message import Message


@dataclass
class Chat:
    chat_id: str
    title: str
    messages: list[Message] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.chat_id.strip():
            raise ValueError("Chat id cannot be empty.")
        if not self.title.strip():
            raise ValueError("Chat title cannot be empty.")

    def add_message(self, message: Message) -> None:
        self.messages.append(message)

    def add_messages(self, messages: list[Message]) -> None:
        self.messages.extend(messages)

    def rename(self, title: str) -> None:
        normalized_title = title.strip()
        if not normalized_title:
            raise ValueError("Chat title cannot be empty.")
        self.title = normalized_title

    def last_message_preview(self) -> str:
        if not self.messages:
            return ""
        return self.messages[-1].content

    def updated_at(self) -> str:
        if not self.messages:
            return "Ahora"
        return self.messages[-1].created_at

    def last_assistant_chunks(self) -> list[str]:
        for message in reversed(self.messages):
            if message.role == "assistant":
                return message.content.split()
        return []
