"""Port for building anonymized visual PDF previews."""
from __future__ import annotations

from abc import ABC, abstractmethod


class AnonymizedPdfBuilderPort(ABC):
    """Define how the orchestrator builds anonymized PDF previews."""

    @abstractmethod
    def build(
        self,
        pdf_content: bytes,
        replacements: dict[str, str],
    ) -> bytes:
        """Build an anonymized PDF from original bytes and replacements.

        Args:
            pdf_content (bytes): The original PDF bytes.
            replacements (dict[str, str]): Placeholder-to-original mappings.

        Returns:
            bytes: The anonymized PDF bytes.

        Raises:
            ValueError: If no visible text can be replaced.
        """
        ...
