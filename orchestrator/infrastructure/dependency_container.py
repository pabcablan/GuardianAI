"""Dependency composition for the orchestrator module."""
from __future__ import annotations

import os
from dataclasses import dataclass

from application.services.anonymization_registry import AnonymizationRegistry
from application.services.document_registry import DocumentRegistry
from infrastructure.adapters.fake_assistant_stream_gateway import (
    FakeAssistantStreamGateway,
)
from infrastructure.adapters.http.ai_gateway_client import HttpAiGatewayClient
from infrastructure.adapters.http.document_processor_client import (
    HttpDocumentProcessingClient,
)
from infrastructure.adapters.http.privacy_shield_client import (
    HttpPrivacyShieldClient,
)
from infrastructure.adapters.pdf.pymupdf_anonymized_pdf_builder import (
    PyMuPdfAnonymizedPdfBuilder,
)
from infrastructure.ports.anonymized_pdf_builder_port import (
    AnonymizedPdfBuilderPort,
)
from infrastructure.ports.ai_gateway_port import AiGatewayPort
from infrastructure.ports.document_processor_port import DocumentProcessorPort
from infrastructure.ports.privacy_shield_port import PrivacyShieldPort


@dataclass(frozen=True)
class OrchestratorContainer:
    """Group the orchestrator dependencies.

    Attributes:
        privacy_shield (PrivacyShieldPort): The privacy-shield client.
        document_processor (DocumentProcessorPort): The document processor
            client.
        ai_gateway (AiGatewayPort): The assistant stream gateway.
        anonymized_pdf_builder (AnonymizedPdfBuilderPort): The visual PDF
            preview builder.
        document_registry (DocumentRegistry): In-memory processed document
            storage.
        anonymization_registry (AnonymizationRegistry): In-memory replacement
            storage.
    """

    privacy_shield: PrivacyShieldPort
    document_processor: DocumentProcessorPort
    ai_gateway: AiGatewayPort
    anonymized_pdf_builder: AnonymizedPdfBuilderPort
    document_registry: DocumentRegistry
    anonymization_registry: AnonymizationRegistry


def build_container() -> OrchestratorContainer:
    """Build the orchestrator dependency graph.

    Returns:
        OrchestratorContainer: The configured dependency container.
    """
    return OrchestratorContainer(
        privacy_shield=HttpPrivacyShieldClient(),
        document_processor=HttpDocumentProcessingClient(),
        ai_gateway=_build_ai_gateway(),
        anonymized_pdf_builder=PyMuPdfAnonymizedPdfBuilder(),
        document_registry=DocumentRegistry(),
        anonymization_registry=AnonymizationRegistry(),
    )


def _build_ai_gateway() -> AiGatewayPort:
    """Build the configured assistant gateway implementation.

    Returns:
        AiGatewayPort: Real or fake gateway depending on the environment mode.
    """
    assistant_mode = os.getenv("ORCHESTRATOR_ASSISTANT_MODE", "fake").lower()
    if assistant_mode == "real":
        return HttpAiGatewayClient()

    return FakeAssistantStreamGateway()
