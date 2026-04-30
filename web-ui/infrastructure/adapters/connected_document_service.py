"""Adapter that connects chats with orchestrator document processing."""
from __future__ import annotations

from collections.abc import Iterator

from application.usecases.attach_document import (
    AttachDocumentCompleted,
    AttachDocumentFailed,
    AttachDocumentProgress,
    AttachDocumentStreamEvent,
)
from infrastructure.ports.external.orchestrator_document_port import (
    OrchestratorDocumentPort,
    ProcessDocumentCompletedEvent,
    ProcessDocumentErrorEvent,
    ProcessDocumentProgressEvent,
    ProcessDocumentRequest,
)
from infrastructure.ports.internal.chat_repository_port import ChatRepositoryPort
from infrastructure.ports.internal.document_service_port import DocumentServicePort


class ConnectedDocumentService(DocumentServicePort):
    """Validate chats before delegating uploaded documents to orchestrator."""

    def __init__(
        self,
        chat_repository: ChatRepositoryPort,
        document_processor: OrchestratorDocumentPort,
    ) -> None:
        """Initialize the document service.

        Args:
            chat_repository (ChatRepositoryPort): The repository used to check
                whether the target chat exists.
            document_processor (OrchestratorDocumentPort): The orchestrator
                document client.
        """
        self._chat_repository = chat_repository
        self._document_processor = document_processor

    def stream_attach_document(
        self,
        chat_id: str,
        filename: str,
        content_type: str,
        content: bytes,
        prompt: str = "",
    ) -> Iterator[AttachDocumentStreamEvent]:
        """Process an attachment and translate orchestrator document events.

        Args:
            chat_id (str): The identifier of the chat that receives the document.
            filename (str): The uploaded document filename.
            content_type (str): The uploaded document MIME type.
            content (bytes): The uploaded document bytes.
            prompt (str): The optional prompt to combine with the document text.

        Returns:
            Iterator[AttachDocumentStreamEvent]: The translated document
            attachment events.

        Raises:
            KeyError: If the target chat does not exist.
        """
        if self._chat_repository.load_chat(chat_id) is None:
            raise KeyError(chat_id)

        for event in self._document_processor.stream_process_document(
            ProcessDocumentRequest(
                filename=filename,
                content_type=content_type,
                content=content,
                prompt=prompt,
            )
        ):
            if isinstance(event, ProcessDocumentProgressEvent):
                yield AttachDocumentProgress(
                    event=event.event,
                    stage=event.stage,
                    current=event.current,
                    total=event.total,
                    message=event.message,
                )
                continue

            if isinstance(event, ProcessDocumentCompletedEvent):
                yield AttachDocumentCompleted(
                    event=event.event,
                    document_id=event.document_id,
                    filename=event.filename,
                )
                continue

            if isinstance(event, ProcessDocumentErrorEvent):
                yield AttachDocumentFailed(
                    event=event.event,
                    detail=event.detail,
                )
