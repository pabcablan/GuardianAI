from __future__ import annotations

from dataclasses import dataclass

from application.usecases.attach_document import AttachDocumentUseCase
from application.usecases.create_chat import CreateChatUseCase
from application.usecases.delete_chat import DeleteChatUseCase
from application.usecases.list_chats import ListChatsUseCase
from application.usecases.load_chat import LoadChatUseCase
from application.usecases.rename_chat import RenameChatUseCase
from application.usecases.send_message import SendMessageUseCase
from application.usecases.stream_response import StreamResponseUseCase
from infrastructure.adapters.in_memory_chat_gateway import InMemoryChatGateway


@dataclass(frozen=True)
class WebUiContainer:
    create_chat: CreateChatUseCase
    list_chats: ListChatsUseCase
    load_chat: LoadChatUseCase
    send_message: SendMessageUseCase
    attach_document: AttachDocumentUseCase
    delete_chat: DeleteChatUseCase
    rename_chat: RenameChatUseCase
    stream_response: StreamResponseUseCase


def build_container() -> WebUiContainer:
    gateway = InMemoryChatGateway()

    return WebUiContainer(
        create_chat=CreateChatUseCase(gateway),
        list_chats=ListChatsUseCase(gateway),
        load_chat=LoadChatUseCase(gateway),
        send_message=SendMessageUseCase(gateway),
        attach_document=AttachDocumentUseCase(gateway),
        delete_chat=DeleteChatUseCase(gateway),
        rename_chat=RenameChatUseCase(gateway),
        stream_response=StreamResponseUseCase(gateway),
    )
