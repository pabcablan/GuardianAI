"""Port for consuming safe response streams from privacy-shield."""
from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Literal, Protocol


@dataclass(frozen=True)
class PrivacyShieldStreamRequest:
    """Represent the data needed to request a safe response stream.

    The web-ui module does not send anonymization maps or extracted document
    text. Privacy-shield owns that data after document processing and exposes
    only a safe stream for the UI to consume.

    Attributes:
        chat_id (str): The chat that will display the response stream.
        document_id (str): The processed document associated with the stream.
    """

    chat_id: str
    document_id: str


@dataclass(frozen=True)
class PrivacyShieldMessageStreamRequest:
    """Represent the data needed to request a message response stream.

    Attributes:
        chat_id (str): The chat that will display the response stream.
        content (str): The user message that should be answered.
    """

    chat_id: str
    content: str


@dataclass(frozen=True)
class PrivacyShieldStreamChunk:
    """Represent one safe text chunk emitted by privacy-shield.

    Attributes:
        event (Literal["chunk"]): The stream event type.
        content (str): The safe deanonymized text chunk.
    """

    event: Literal["chunk"]
    content: str


@dataclass(frozen=True)
class PrivacyShieldStreamCompleted:
    """Represent the successful end of a privacy-shield stream.

    Attributes:
        event (Literal["completed"]): The stream event type.
    """

    event: Literal["completed"]


@dataclass(frozen=True)
class PrivacyShieldStreamFailed:
    """Represent an error emitted by privacy-shield.

    Attributes:
        event (Literal["error"]): The stream event type.
        detail (str): The error detail.
    """

    event: Literal["error"]
    detail: str


PrivacyShieldStreamEvent = (
    PrivacyShieldStreamChunk
    | PrivacyShieldStreamCompleted
    | PrivacyShieldStreamFailed
)


class PrivacyShieldPort(Protocol):
    """Define how web-ui consumes safe streams from privacy-shield."""

    def stream_safe_response(
        self,
        request: PrivacyShieldStreamRequest,
    ) -> Iterator[PrivacyShieldStreamEvent]:
        """Stream safe response events for a processed document.

        Args:
            request (PrivacyShieldStreamRequest): The chat and processed
            document identifiers needed to locate the stream.

        Returns:
            Iterator[PrivacyShieldStreamEvent]: Safe text chunks and terminal
            stream events emitted by privacy-shield.
        """

    def stream_message_response(
        self,
        request: PrivacyShieldMessageStreamRequest,
    ) -> Iterator[PrivacyShieldStreamEvent]:
        """Stream safe response events for a user chat message.

        Args:
            request (PrivacyShieldMessageStreamRequest): The chat identifier and
            user message that should be answered.

        Returns:
            Iterator[PrivacyShieldStreamEvent]: Safe text chunks and terminal
            stream events emitted by privacy-shield.
        """
