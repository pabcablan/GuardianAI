"""Dependency composition for the web-ui module."""
from __future__ import annotations

from dataclasses import dataclass

from application.usecases.attach_document import AttachDocumentUseCase
from application.usecases.create_chat import CreateChatUseCase
from application.usecases.delete_chat import DeleteChatUseCase
from application.usecases.list_chats import ListChatsUseCase
from application.usecases.load_chat import LoadChatUseCase
from application.usecases.rename_chat import RenameChatUseCase
from application.usecases.stream_message_response import (
    StreamMessageResponseUseCase,
)
from application.usecases.stream_safe_response import StreamSafeResponseUseCase
from infrastructure.adapters.connected_document_service import (
    ConnectedDocumentService,
)
from infrastructure.adapters.mongodb.client import build_mongo_database
from infrastructure.adapters.mongodb.mongo_chat_gateway import MongoChatGateway
from infrastructure.adapters.orchestrator.document_client import (
    HttpOrchestratorDocumentClient,
)
from infrastructure.adapters.orchestrator.response_client import (
    HttpOrchestratorResponseClient,
)
from infrastructure.ports.internal.chat_repository_port import (
    ChatRepositoryPort,
)


@dataclass(frozen=True)
class WebUiContainer:
    """Group the dependencies exposed by the web-ui API."""

    create_chat: CreateChatUseCase
    list_chats: ListChatsUseCase
    load_chat: LoadChatUseCase
    attach_document: AttachDocumentUseCase
    delete_chat: DeleteChatUseCase
    rename_chat: RenameChatUseCase
    stream_safe_response: StreamSafeResponseUseCase
    stream_message_response: StreamMessageResponseUseCase
    chat_repository: ChatRepositoryPort
    orchestrator_response: HttpOrchestratorResponseClient


def build_container() -> WebUiContainer:
    """Build the dependency graph for the web-ui backend.

    Returns:
        WebUiContainer: The configured use case container.
    """
    database = build_mongo_database()
    gateway = MongoChatGateway(database)
    orchestrator_response = HttpOrchestratorResponseClient()
    orchestrator_document = HttpOrchestratorDocumentClient()
    document_service = ConnectedDocumentService(gateway, orchestrator_document)

    return WebUiContainer(
        create_chat=CreateChatUseCase(gateway),
        list_chats=ListChatsUseCase(gateway),
        load_chat=LoadChatUseCase(gateway),
        attach_document=AttachDocumentUseCase(document_service),
        delete_chat=DeleteChatUseCase(gateway),
        rename_chat=RenameChatUseCase(gateway),
        stream_safe_response=StreamSafeResponseUseCase(orchestrator_response),
        stream_message_response=StreamMessageResponseUseCase(
            orchestrator_response,
        ),
        chat_repository=gateway,
        orchestrator_response=orchestrator_response,
    )
