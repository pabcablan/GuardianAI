from uuid import UUID, uuid4
from dataclasses import dataclass


@dataclass(frozen=True)
class SessionId:
    value: UUID

    @classmethod
    def generate(cls) -> "SessionId":
        return cls(value=uuid4())

    @classmethod
    def from_string(cls, value: str) -> "SessionId":
        return cls(value=UUID(value))

    def __str__(self) -> str:
        return str(self.value)