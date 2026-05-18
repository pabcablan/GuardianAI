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
        self._messages.create_index("document_id", sparse=True)

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
                anonymization_replacements=message.get(
                    "anonymization_replacements"
                ),
                document_id=message.get("document_id"),
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
        """Soft-delete a chat and remove its stored messages."""
        self._chats.update_one(
            {"chat_id": chat_id},
            {
                "$set": {
                    "deleted": True,
                    "updated_at": self._now(),
                }
            },
        )
        self._messages.delete_many({"chat_id": chat_id})

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
                "anonymization_replacements": (
                    message.anonymization_replacements
                ),
                "document_id": message.document_id,
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
        anonymization_replacements: dict[str, str] | None = None,
    ) -> None:
        """Store the anonymized text for one message."""
        update_fields: dict[str, object] = {
            "anonymized_content": anonymized_content,
        }
        if anonymization_replacements is not None:
            update_fields["anonymization_replacements"] = (
                anonymization_replacements
            )
        result = self._messages.update_one(
            {"message_id": message_id},
            {"$set": update_fields},
        )
        if result.matched_count == 0:
            raise KeyError(message_id)

    def link_document_to_message(
        self,
        document_id: str,
        message_id: str,
    ) -> None:
        """Persist the processed document linked to one user message."""
        result = self._messages.update_one(
            {"message_id": message_id},
            {"$set": {"document_id": document_id}},
        )
        if result.matched_count == 0:
            raise KeyError(message_id)

    def get_user_message_id_by_document(
        self,
        document_id: str,
    ) -> str | None:
        """Return the user message linked to one processed document."""
        message = self._messages.find_one(
            {"document_id": document_id},
            projection={"message_id": 1},
        )
        if message is None:
            return None
        return str(message["message_id"])

    def get_chat_replacements(self, chat_id: str) -> dict[str, str]:
        """Return all anonymization replacements stored for a chat."""
        replacements: dict[str, str] = {}
        for message in self._messages.find(
            {"chat_id": chat_id},
            projection={"anonymization_replacements": 1},
        ):
            raw_replacements = message.get("anonymization_replacements")
            if not isinstance(raw_replacements, dict):
                continue

            replacements.update(
                {
                    str(placeholder): str(original)
                    for placeholder, original in raw_replacements.items()
                }
            )

        return replacements
