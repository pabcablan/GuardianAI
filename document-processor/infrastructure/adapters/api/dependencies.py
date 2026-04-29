from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from application.usecases.extract_document import ExtractDocumentUseCase
from infrastructure.adapters.local_document_extractor import \
    LocalDocumentExtractor


@dataclass(frozen=True)
class DocumentProcessorContainer:
    extract_document: ExtractDocumentUseCase


def build_container() -> DocumentProcessorContainer:
    storage_dir = Path("document-processor") / "storage"
    extractor = LocalDocumentExtractor(storage_dir=storage_dir)
    return DocumentProcessorContainer(
        extract_document=ExtractDocumentUseCase(extractor),
    )
