"""MongoDB gateway for chats."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from pymongo.database import Database

from application.usecases.create_chat import CreateChatResult
from application.usecases.list_chats import ChatSummary
from domain.chat import Chat
from domain.message import Message
from infrastructure.ports.internal.chat_repository_port import ChatRepositoryPort


class MongoChatGateway(ChatRepositoryPort):
    """Implement chat storage using MongoDB."""

    def __init__(self, database: Database) -> None:
        """Initialize the MongoDB collections and indexes."""
        self._chats = database["chats"]
        self._messages = database["messages"]

        self._chats.create_index("chat_id", unique=True)
        self._chats.create_index("updated_at")
        self._messages.create_index("message_id", unique=True)
        self._messages.create_index([("chat_id", 1), ("created_at", 1)])

    def create_chat(self, title: str) -> CreateChatResult:
        """Create and persist a new chat."""
        chat_id = f"chat-{uuid4().hex}"
        now = self._now()

        self._chats.insert_one(
            {
                "chat_id": chat_id,
                "title": title,
                "created_at": now,
                "updated_at": now,
                "deleted": False,
            }
        )

        return CreateChatResult(chat_id=chat_id, title=title)

    def list_chats(self) -> list[ChatSummary]:
        """Return stored chat summaries."""
        summaries: list[ChatSummary] = []

        for chat in self._chats.find(
            {"deleted": False},
            sort=[("updated_at", -1)],
        ):
            last_message = self._messages.find_one(
                {"chat_id": chat["chat_id"]},
                sort=[("created_at", -1)],
            )

            summaries.append(
                ChatSummary(
                    chat_id=chat["chat_id"],
                    title=chat["title"],
                    last_message_preview=(
                        last_message["content"] if last_message else ""
                    ),
                    updated_at=(
                        last_message["created_at"]
                        if last_message
                        else chat["updated_at"]
                    ),
                )
            )

        return summaries

    def load_chat(self, chat_id: str) -> Chat | None:
        """Load one chat and its ordered message history."""
        chat = self._chats.find_one(
            {
                "chat_id": chat_id,
                "deleted": False,
            }
        )

        if chat is None:
            return None

        messages = [
            Message(
                message_id=message["message_id"],
                role=message["role"],
                content=message["content"],
                created_at=message["created_at"],
                anonymized_content=message.get("anonymized_content"),
            )
            for message in self._messages.find(
                {"chat_id": chat_id},
                sort=[("created_at", 1)],
            )
        ]

        return Chat(
            chat_id=chat["chat_id"],
            title=chat["title"],
            messages=messages,
        )

    def delete_chat(self, chat_id: str) -> None:
        """Soft-delete a chat."""
        self._chats.update_one(
            {"chat_id": chat_id},
            {
                "$set": {
                    "deleted": True,
                    "updated_at": self._now(),
                }
            },
        )

    def rename_chat(self, chat_id: str, title: str) -> None:
        """Rename an existing chat."""
        result = self._chats.update_one(
            {
                "chat_id": chat_id,
                "deleted": False,
            },
            {
                "$set": {
                    "title": title,
                    "updated_at": self._now(),
                }
            },
        )

        if result.matched_count == 0:
            raise KeyError(chat_id)

    def append_message(self, chat_id: str, message: Message) -> None:
        """Append one message to a chat."""
        chat = self._chats.find_one(
            {
                "chat_id": chat_id,
                "deleted": False,
            }
        )

        if chat is None:
            raise KeyError(chat_id)

        self._messages.insert_one(
            {
                "message_id": message.message_id,
                "chat_id": chat_id,
                "role": message.role,
                "content": message.content,
                "created_at": message.created_at,
                "anonymized_content": message.anonymized_content,
            }
        )

        self._chats.update_one(
            {"chat_id": chat_id},
            {"$set": {"updated_at": message.created_at}},
        )

    def _now(self) -> str:
        """Return an UTC timestamp."""
        return datetime.now(timezone.utc).isoformat()

    def update_message_anonymized_content(
        self,
        message_id: str,
        anonymized_content: str,
    ) -> None:
        """Store the anonymized text for one message."""
        result = self._messages.update_one(
            {"message_id": message_id},
            {"$set": {"anonymized_content": anonymized_content}},
        )
        if result.matched_count == 0:
            raise KeyError(message_id)
