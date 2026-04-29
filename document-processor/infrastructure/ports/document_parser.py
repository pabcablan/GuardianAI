from typing import Protocol, Any

from domain.parsed_document import ParsedDocument

class DocumentParser(Protocol):
    def parse(self, file: Any) -> ParsedDocument:
        ...
