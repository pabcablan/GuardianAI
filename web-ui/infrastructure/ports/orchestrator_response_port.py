"""Port for consuming safe response streams from orchestrator."""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator

from infrastructure.ports.orchestrator_response_types import (
    OrchestratorAnonymizationPreview,
    OrchestratorAnonymizationPreviewRequest,
    OrchestratorAnonymizedPdfPreview,
    OrchestratorAnonymizedResponseRequest,
    OrchestratorDocumentAnonymizationPreviewRequest,
    OrchestratorDocumentResponseRequest,
    OrchestratorMessageResponseRequest,
    OrchestratorStreamEvent,
)


class OrchestratorResponsePort(ABC):
    """Define how web-ui consumes safe streams from orchestrator."""

    @abstractmethod
    def preview_message_anonymization(
        self,
        request: OrchestratorAnonymizationPreviewRequest,
    ) -> OrchestratorAnonymizationPreview:
        """Return anonymized text without calling the assistant."""
        ...

    @abstractmethod
    def preview_document_anonymization(
        self,
        request: OrchestratorDocumentAnonymizationPreviewRequest,
    ) -> OrchestratorAnonymizationPreview:
        """Return an anonymized processed document without calling the assistant."""
        ...

    @abstractmethod
    def get_anonymized_pdf_preview(
        self,
        document_id: str,
        anonymization_id: str,
    ) -> OrchestratorAnonymizedPdfPreview:
        """Return a visual anonymized PDF preview."""
        ...

    @abstractmethod
    def stream_anonymized_response(
        self,
        request: OrchestratorAnonymizedResponseRequest,
    ) -> Iterator[OrchestratorStreamEvent]:
        """Stream a response from already anonymized text."""
        ...

    @abstractmethod
    def stream_safe_response(
        self,
        request: OrchestratorDocumentResponseRequest,
    ) -> Iterator[OrchestratorStreamEvent]:
        """Stream safe response events for a processed document."""
        ...

    @abstractmethod
    def stream_message_response(
        self,
        request: OrchestratorMessageResponseRequest,
    ) -> Iterator[OrchestratorStreamEvent]:
        """Stream a safe assistant response for a user chat message."""
        ...
