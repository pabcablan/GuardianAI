from __future__ import annotations

from collections.abc import Iterator

from application.usecases.attach_document import (
    AttachDocumentCompleted,
    AttachDocumentFailed,
    AttachDocumentProgress,
    AttachDocumentResult,
    AttachDocumentStreamEvent,
)
from infrastructure.ports.external.document_processing_port import (
    DocumentProcessingPort,
    ExtractDocumentCompletedEvent,
    ExtractDocumentErrorEvent,
    ExtractDocumentProgressEvent,
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

    def stream_attach_document(
        self,
        chat_id: str,
        filename: str,
        content_type: str,
        content: bytes,
    ) -> Iterator[AttachDocumentStreamEvent]:
        if self._chat_repository.load_chat(chat_id) is None:
            raise KeyError(chat_id)

        for event in self._document_processor.stream_extract_document(
            ExtractDocumentRequest(
                filename=filename,
                content_type=content_type,
                content=content,
            )
        ):
            if isinstance(event, ExtractDocumentProgressEvent):
                yield AttachDocumentProgress(
                    event=event.event,
                    stage=event.stage,
                    current=event.current,
                    total=event.total,
                    message=event.message,
                )
                continue

            if isinstance(event, ExtractDocumentCompletedEvent):
                yield AttachDocumentCompleted(
                    event=event.event,
                    document_id=event.document_id,
                    filename=event.filename,
                )
                continue

            if isinstance(event, ExtractDocumentErrorEvent):
                yield AttachDocumentFailed(
                    event=event.event,
                    detail=event.detail,
                )
