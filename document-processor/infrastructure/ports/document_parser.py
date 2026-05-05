"""Port that defines document parsing."""
from __future__ import annotations

from typing import Any, Protocol

from domain.parsed_document import ParsedDocument


class DocumentParser(Protocol):
    """Define the contract for document parsers."""

    async def parse(self, uploaded_file: Any) -> ParsedDocument:
        """Parse a document file into the domain representation.

        Args:
            uploaded_file (Any): The uploaded document object.

        Returns:
            ParsedDocument: The parsed document metadata and content.
        """
        ...
