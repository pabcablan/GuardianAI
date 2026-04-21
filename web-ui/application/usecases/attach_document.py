from __future__ import annotations

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
class AttachDocumentResult:
    document_id: str
    filename: str

class AttachDocumentUseCase:
    def __init__(self, gateway: DocumentServicePort) -> None:
        self._gateway = gateway

    def execute(self, command: AttachDocumentCommand) -> AttachDocumentResult:
        document = DocumentAttachment(
            filename=command.filename,
            content_type=command.content_type,
            content=command.content,
        )

        return self._gateway.attach_document(
            chat_id=command.chat_id,
            filename=document.filename,
            content_type=document.content_type,
            content=document.content,
        )
