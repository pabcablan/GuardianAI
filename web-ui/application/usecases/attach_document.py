"""Use case for attaching PDF documents to a chat conversation."""
from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from domain.document import DocumentAttachment
from infrastructure.ports.internal.document_service_port import DocumentServicePort


@dataclass(frozen=True)
class AttachDocumentCommand:
    """Represent the input required to attach a document.

    Attributes:
        chat_id (str): The identifier of the chat that receives the document.
        filename (str): The original document filename.
        content_type (str): The MIME type reported by the upload client.
        content (bytes): The binary document content.
        prompt (str): The optional user prompt attached to the document.
    """

    chat_id: str
    filename: str
    content_type: str
    content: bytes
    prompt: str = ""


@dataclass(frozen=True)
class AttachDocumentProgress:
    """Represent a progress event emitted while processing a document.

    Attributes:
        event (str): The event type.
        stage (str): The current processing stage.
        current (int): The current progress value.
        total (int): The total progress value.
        message (str): A human-readable progress message.
    """

    event: str
    stage: str
    current: int
    total: int
    message: str


@dataclass(frozen=True)
class AttachDocumentCompleted:
    """Represent a successful document attachment event.

    Attributes:
        event (str): The event type.
        document_id (str): The identifier assigned to the processed document.
        filename (str): The processed document filename.
    """

    event: str
    document_id: str
    filename: str


@dataclass(frozen=True)
class AttachDocumentFailed:
    """Represent a failed document attachment event.

    Attributes:
        event (str): The event type.
        detail (str): The error detail returned by the processor.
    """

    event: str
    detail: str


AttachDocumentStreamEvent = (
    AttachDocumentProgress | AttachDocumentCompleted | AttachDocumentFailed
)


class AttachDocumentUseCase:
    """Coordinate document validation and attachment."""

    def __init__(self, gateway: DocumentServicePort) -> None:
        """Initialize the use case.

        Args:
            gateway (DocumentServicePort): The document service used to attach
                and process uploaded documents.
        """
        self._gateway = gateway

    def stream(self, command: AttachDocumentCommand) -> Iterator[AttachDocumentStreamEvent]:
        """Attach a document and stream processing events.

        Args:
            command (AttachDocumentCommand): The attachment request data.

        Returns:
            Iterator[AttachDocumentStreamEvent]: The document processing events.
        """
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
            prompt=command.prompt,
        )
