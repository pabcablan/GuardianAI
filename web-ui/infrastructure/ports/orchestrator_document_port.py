"""Port for sending document uploads through orchestrator."""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator

from infrastructure.ports.orchestrator_document_types import (
    OrchestratorDocumentEvent,
    ProcessDocumentRequest,
)


class OrchestratorDocumentPort(ABC):
    """Define document processing operations exposed by orchestrator."""

    @abstractmethod
    def stream_process_document(
        self,
        request: ProcessDocumentRequest,
    ) -> Iterator[OrchestratorDocumentEvent]:
        """Stream document processing events."""
        ...
