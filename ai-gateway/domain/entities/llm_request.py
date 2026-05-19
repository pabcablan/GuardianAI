"""Domain entity that tracks one provider request lifecycle."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from domain.value_objects.message import Message


class RequestStatus(Enum):
    """Lifecycle states for one LLM request."""

    PENDING = "pending"
    SENT = "sent"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class LLMRequest:
    """Represent one request sent to the upstream provider.

    Attributes:
        id (str): The request identifier.
        org_id (str): The owning organization identifier.
        messages (list[Message]): The normalized request messages.
        model (str): The provider model identifier.
        created_at (datetime): The request creation timestamp.
        status (RequestStatus): The request lifecycle status.
        failure_reason (str | None): Optional failure detail.
    """

    id: str
    org_id: str
    messages: list[Message]
    model: str
    created_at: datetime
    status: RequestStatus = field(default=RequestStatus.PENDING)
    failure_reason: str | None = field(default=None)

    def complete(self, finish_reason: str) -> None:
        """Mark the request as completed.

        Args:
            finish_reason (str): The provider finish reason.

        Raises:
            ValueError: If the request was not previously marked as sent.
        """
        if self.status != RequestStatus.SENT:
            raise ValueError(
                f"Cannot complete a request with status {self.status}",
            )
        self.status = RequestStatus.COMPLETED

    def fail(self, reason: str) -> None:
        """Mark the request as failed.

        Args:
            reason (str): The failure detail.

        Raises:
            ValueError: If the request was already completed.
        """
        if self.status == RequestStatus.COMPLETED:
            raise ValueError("Cannot fail a completed request")
        self.status = RequestStatus.FAILED
        self.failure_reason = reason

    def mark_sent(self) -> None:
        """Mark the request as sent to the provider.

        Raises:
            ValueError: If the request was not pending.
        """
        if self.status != RequestStatus.PENDING:
            raise ValueError(
                f"Cannot mark as sent a request with status {self.status}",
            )
        self.status = RequestStatus.SENT
