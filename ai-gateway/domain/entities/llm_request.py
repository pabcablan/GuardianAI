from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List
from ..value_objects.message import Message


class RequestStatus(Enum):
    PENDING = "pending"
    SENT = "sent"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class LLMRequest:
    id: str
    org_id: str
    messages: List[Message]
    model: str
    created_at: datetime
    status: RequestStatus = field(default=RequestStatus.PENDING)
    failure_reason: str | None = field(default=None)

    def complete(self, finish_reason: str) -> None:
        if self.status != RequestStatus.SENT:
            raise ValueError(f"Cannot complete a request with status {self.status}")
        self.status = RequestStatus.COMPLETED

    def fail(self, reason: str) -> None:
        if self.status == RequestStatus.COMPLETED:
            raise ValueError("Cannot fail a completed request")
        self.status = RequestStatus.FAILED
        self.failure_reason = reason

    def mark_sent(self) -> None:
        if self.status != RequestStatus.PENDING:
            raise ValueError(f"Cannot mark as sent a request with status {self.status}")
        self.status = RequestStatus.SENT