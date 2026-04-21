from __future__ import annotations

from dataclasses import replace

from application.usecases.attach_document import AttachDocumentResult
from application.usecases.create_chat import CreateChatResult
from application.usecases.list_chats import ChatSummary
from application.usecases.load_chat import ChatDetail
from application.usecases.send_message import SendMessageResult
from domain.chat import Chat
from domain.message import Message
from infrastructure.ports.internal.chat_repository_port import ChatRepositoryPort
from infrastructure.ports.internal.document_service_port import DocumentServicePort
from infrastructure.ports.internal.message_service_port import MessageServicePort
from infrastructure.ports.internal.stream_service_port import StreamServicePort


class InMemoryChatGateway(
    ChatRepositoryPort,
    MessageServicePort,
    DocumentServicePort,
    StreamServicePort,
):
    def __init__(self) -> None:
        self._chats: dict[str, Chat] = {}

    def create_chat(self, title: str) -> CreateChatResult:
        chat_id = f"chat-{self._generate_id()}"
        self._chats[chat_id] = Chat(chat_id=chat_id, title=title, messages=[])
        return CreateChatResult(chat_id=chat_id, title=title)

    def list_chats(self) -> list[ChatSummary]:
        summaries: list[ChatSummary] = []
        for chat in self._chats.values():
            summaries.append(
                ChatSummary(
                    chat_id=chat.chat_id,
                    title=chat.title,
                    last_message_preview=chat.last_message_preview(),
                    updated_at=chat.updated_at(),
                )
            )
        return summaries

    def load_chat(self, chat_id: str) -> ChatDetail | None:
        chat = self._chats.get(chat_id)
        if chat is None:
            return None

        return replace(chat, messages=[replace(message) for message in chat.messages])

    def send_message(self, chat_id: str, content: str) -> SendMessageResult:
        chat = self._require_chat(chat_id)
        user_message = Message(
            message_id=f"msg-{self._generate_id()}",
            role="user",
            content=content,
            created_at="Ahora",
        )
        assistant_message = Message(
            message_id=f"msg-{self._generate_id()}",
            role="assistant",
            content=self._build_assistant_reply(content),
            created_at="Ahora",
        )

        chat.add_messages([user_message, assistant_message])

        return SendMessageResult(
            user_message_id=user_message.message_id,
            assistant_message_id=assistant_message.message_id,
            assistant_content=assistant_message.content,
        )

    def attach_document(
        self,
        chat_id: str,
        filename: str,
        content_type: str,
        content: bytes,
    ) -> AttachDocumentResult:
        self._require_chat(chat_id)
        document_id = f"doc-{self._generate_id()}"
        _ = (content_type, content)
        return AttachDocumentResult(document_id=document_id, filename=filename)

    def delete_chat(self, chat_id: str) -> None:
        self._chats.pop(chat_id, None)

    def rename_chat(self, chat_id: str, title: str) -> None:
        chat = self._require_chat(chat_id)
        chat.rename(title)

    def stream_response(self, chat_id: str) -> list[str]:
        chat = self._require_chat(chat_id)
        return chat.last_assistant_chunks()

    def _require_chat(self, chat_id: str) -> Chat:
        chat = self._chats.get(chat_id)
        if chat is None:
            raise KeyError(chat_id)
        return chat

    def _generate_id(self) -> str:
        from uuid import uuid4

        return uuid4().hex

    def _build_assistant_reply(self, prompt: str) -> str:
        normalized_prompt = prompt.strip()
        if not normalized_prompt:
            return "Necesito un mensaje para poder responder."

        return (
            f'Respuesta simulada para "{normalized_prompt}". '
            "Cuando el resto de modulos esten conectados, esta respuesta "
            "saldra del backend real del sistema."
        )
