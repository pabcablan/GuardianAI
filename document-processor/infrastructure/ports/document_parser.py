"""
Defines the contract for a document parser.
Its responsible for parsing a document file and returning a ParsedDocument object
with its metadata and content.
"""

from typing import Protocol, Any

from domain.parsed_document import ParsedDocument

class DocumentParser(Protocol):
    def parse(self, uploaded_file: Any) -> ParsedDocument:
        """
        Parses a document file and returns a ParsedDocument
        
        Args:
            uploaded_file: The document file to parse. Its type is any since it can be
            obtained from various sources.
        Returns:
            A ParsedDocument object containing the metadata and content of the parsed document.
        """
        ...
