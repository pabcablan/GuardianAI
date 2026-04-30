from dataclasses import dataclass
from enum import Enum
from .anonymized_text import AnonymizedText


class Role(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass(frozen=True)
class Message:
    role: Role
    content: AnonymizedText

    def to_dict(self) -> dict:
        return {
            "role": self.role.value,
            "content": str(self.content)
        }