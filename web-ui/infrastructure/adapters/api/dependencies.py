"""Dependency composition for the web-ui API."""
from __future__ import annotations

from dataclasses import dataclass

from application.usecases.attach_document import AttachDocumentUseCase
from application.usecases.create_chat import CreateChatUseCase
from application.usecases.delete_chat import DeleteChatUseCase
from application.usecases.list_chats import ListChatsUseCase
from application.usecases.load_chat import LoadChatUseCase
from application.usecases.rename_chat import RenameChatUseCase
from application.usecases.stream_message_response import \
    StreamMessageResponseUseCase
from application.usecases.stream_safe_response import StreamSafeResponseUseCase
from infrastructure.adapters.connected_document_service import \
    ConnectedDocumentService
from infrastructure.adapters.fake_privacy_shield_client import \
    FakePrivacyShieldClient
from infrastructure.adapters.http_document_processing_client import \
    HttpDocumentProcessingClient
from infrastructure.adapters.http_privacy_shield_client import \
    HttpPrivacyShieldClient
from infrastructure.adapters.in_memory_chat_gateway import InMemoryChatGateway


@dataclass(frozen=True)
class WebUiContainer:
    """Group the use cases exposed by the API.

    Attributes:
        create_chat (CreateChatUseCase): The create chat use case.
        list_chats (ListChatsUseCase): The list chats use case.
        load_chat (LoadChatUseCase): The load chat use case.
        attach_document (AttachDocumentUseCase): The attach document use case.
        delete_chat (DeleteChatUseCase): The delete chat use case.
        rename_chat (RenameChatUseCase): The rename chat use case.
        stream_safe_response (StreamSafeResponseUseCase): The safe response
            stream use case.
        stream_message_response (StreamMessageResponseUseCase): The streamed
            message response use case.
    """

    create_chat: CreateChatUseCase
    list_chats: ListChatsUseCase
    load_chat: LoadChatUseCase
    attach_document: AttachDocumentUseCase
    delete_chat: DeleteChatUseCase
    rename_chat: RenameChatUseCase
    stream_safe_response: StreamSafeResponseUseCase
    stream_message_response: StreamMessageResponseUseCase


def build_container() -> WebUiContainer:
    """Build the dependency graph for the web-ui backend.

    Returns:
        WebUiContainer: The configured use case container.
    """
    gateway = InMemoryChatGateway()
    document_processor = HttpDocumentProcessingClient()
    document_service = ConnectedDocumentService(gateway, document_processor)
    privacy_shield = FakePrivacyShieldClient() # privacy_shield = HttpPrivacyShieldClient()

    return WebUiContainer(
        create_chat=CreateChatUseCase(gateway),
        list_chats=ListChatsUseCase(gateway),
        load_chat=LoadChatUseCase(gateway),
        attach_document=AttachDocumentUseCase(document_service),
        delete_chat=DeleteChatUseCase(gateway),
        rename_chat=RenameChatUseCase(gateway),
        stream_safe_response=StreamSafeResponseUseCase(privacy_shield),
        stream_message_response=StreamMessageResponseUseCase(privacy_shield),
    )
