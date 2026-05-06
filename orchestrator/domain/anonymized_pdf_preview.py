"""Domain data for anonymized PDF previews."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AnonymizedPdfPreview:
    """Represent an anonymized PDF preview.

    Attributes:
        filename (str): The preview filename.
        content (bytes): The generated PDF bytes.
    """

    filename: str
    content: bytes
