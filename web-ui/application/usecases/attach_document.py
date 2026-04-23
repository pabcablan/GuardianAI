from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from domain.document import DocumentAttachment
from infrastructure.ports.internal.document_service_port import DocumentServicePort


@dataclass(frozen=True)
class AttachDocumentCommand:
    chat_id: str
    filename: str
    content_type: str
    content: bytes


@dataclass(frozen=True)
class AttachDocumentProgress:
    event: str
    stage: str
    current: int
    total: int
    message: str


@dataclass(frozen=True)
class AttachDocumentCompleted:
    event: str
    document_id: str
    filename: str


@dataclass(frozen=True)
class AttachDocumentFailed:
    event: str
    detail: str


AttachDocumentStreamEvent = (
    AttachDocumentProgress | AttachDocumentCompleted | AttachDocumentFailed
)


class AttachDocumentUseCase:
    def __init__(self, gateway: DocumentServicePort) -> None:
        self._gateway = gateway

    def stream(self, command: AttachDocumentCommand) -> Iterator[AttachDocumentStreamEvent]:
        document = DocumentAttachment(
            filename=command.filename,
            content_type=command.content_type,
            content=command.content,
        )

        return self._gateway.stream_attach_document(
            chat_id=command.chat_id,
            filename=document.filename,
            content_type=document.content_type,
            content=document.content,
        )
