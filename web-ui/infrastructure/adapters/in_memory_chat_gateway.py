"""In-memory gateway for chats, messages, and simulated responses."""
from __future__ import annotations

from dataclasses import replace

from application.usecases.create_chat import CreateChatResult
from application.usecases.list_chats import ChatSummary
from application.usecases.load_chat import ChatDetail
from application.usecases.send_message import SendMessageResult
from domain.chat import Chat
from domain.message import Message
from infrastructure.ports.internal.chat_repository_port import ChatRepositoryPort
from infrastructure.ports.internal.message_service_port import MessageServicePort
from infrastructure.ports.internal.stream_service_port import StreamServicePort


class InMemoryChatGateway(
    ChatRepositoryPort,
    MessageServicePort,
    StreamServicePort,
):
    """Implement the main web-ui ports using volatile in-memory storage."""

    def __init__(self) -> None:
        """Initialize the in-memory chat store."""
        self._chats: dict[str, Chat] = {}

    def create_chat(self, title: str) -> CreateChatResult:
        """Create a new chat and store it in memory.

        Args:
            title (str): The normalized chat title.

        Returns:
            CreateChatResult: The created chat data.
        """
        chat_id = f"chat-{self._generate_id()}"
        self._chats[chat_id] = Chat(chat_id=chat_id, title=title, messages=[])
        return CreateChatResult(chat_id=chat_id, title=title)

    def list_chats(self) -> list[ChatSummary]:
        """Return summaries for all stored chats.

        Returns:
            list[ChatSummary]: The stored chat summaries.
        """
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
        """Return a copied chat to avoid external mutations.

        Args:
            chat_id (str): The identifier of the chat to load.

        Returns:
            ChatDetail | None: The copied chat, or None when it does not exist.
        """
        chat = self._chats.get(chat_id)
        if chat is None:
            return None

        return replace(chat, messages=[replace(message) for message in chat.messages])

    def send_message(self, chat_id: str, content: str) -> SendMessageResult:
        """Store a user message and a simulated assistant response.

        Args:
            chat_id (str): The identifier of the target chat.
            content (str): The normalized user message content.

        Returns:
            SendMessageResult: The generated message identifiers and response.

        Raises:
            KeyError: If the target chat does not exist.
        """
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

    def delete_chat(self, chat_id: str) -> None:
        """Delete a chat when it exists.

        Args:
            chat_id (str): The identifier of the chat to delete.
        """
        self._chats.pop(chat_id, None)

    def rename_chat(self, chat_id: str, title: str) -> None:
        """Update the title of an existing chat.

        Args:
            chat_id (str): The identifier of the chat to rename.
            title (str): The normalized chat title.

        Raises:
            KeyError: If the target chat does not exist.
        """
        chat = self._require_chat(chat_id)
        chat.rename(title)

    def stream_response(self, chat_id: str) -> list[str]:
        """Return chunks from the latest assistant response.

        Args:
            chat_id (str): The identifier of the chat.

        Returns:
            list[str]: The latest assistant response chunks.

        Raises:
            KeyError: If the target chat does not exist.
        """
        chat = self._require_chat(chat_id)
        return chat.last_assistant_chunks()

    def _require_chat(self, chat_id: str) -> Chat:
        """Return a chat or raise when it is not registered.

        Args:
            chat_id (str): The identifier of the chat to retrieve.

        Returns:
            Chat: The stored chat.

        Raises:
            KeyError: If the target chat does not exist.
        """
        chat = self._chats.get(chat_id)
        if chat is None:
            raise KeyError(chat_id)
        return chat

    def _generate_id(self) -> str:
        """Generate a unique identifier suffix.

        Returns:
            str: A UUID-based hexadecimal identifier.
        """
        from uuid import uuid4

        return uuid4().hex

    def _build_assistant_reply(self, prompt: str) -> str:
        """Build a simulated response until a real LLM is connected.

        Args:
            prompt (str): The user prompt.

        Returns:
            str: The simulated assistant response.
        """
        normalized_prompt = prompt.strip()
        if not normalized_prompt:
            return "Necesito un mensaje para poder responder."

        return (
            f'Respuesta simulada para "{normalized_prompt}". '
            "Cuando el resto de modulos esten conectados, esta respuesta "
            "saldra del backend real del sistema."
        )
