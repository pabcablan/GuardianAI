from abc import ABC, abstractmethod
from typing import Any

from domain.parsed_document import ParsedDocument


class DocumentParser(ABC):
    """Contract for components that parse uploaded documents."""

    @abstractmethod
    async def parse(self, uploaded_file: Any) -> ParsedDocument:
        """Parse an incoming document into the internal domain model.

        Args:
            uploaded_file (Any): File-like object received from an external source.

        Returns:
            ParsedDocument: Parsed document metadata and raw binary content.
        """
        ...
