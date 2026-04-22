from __future__ import annotations

from application.usecases.attach_document import AttachDocumentResult
from infrastructure.ports.external.document_processing_port import (
    DocumentProcessingPort,
    ExtractDocumentRequest,
)
from infrastructure.ports.internal.chat_repository_port import ChatRepositoryPort
from infrastructure.ports.internal.document_service_port import DocumentServicePort


class ConnectedDocumentService(DocumentServicePort):
    def __init__(
        self,
        chat_repository: ChatRepositoryPort,
        document_processor: DocumentProcessingPort,
    ) -> None:
        self._chat_repository = chat_repository
        self._document_processor = document_processor

    def attach_document(
        self,
        chat_id: str,
        filename: str,
        content_type: str,
        content: bytes,
    ) -> AttachDocumentResult:
        if self._chat_repository.load_chat(chat_id) is None:
            raise KeyError(chat_id)

        result = self._document_processor.extract_document(
            ExtractDocumentRequest(
                filename=filename,
                content_type=content_type,
                content=content,
            )
        )
        return AttachDocumentResult(
            document_id=result.document_id,
            filename=result.filename,
        )
