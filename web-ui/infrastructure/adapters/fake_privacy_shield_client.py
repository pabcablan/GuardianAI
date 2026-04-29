"""Fake privacy-shield client used until the real module is connected."""
from __future__ import annotations

import time
from collections.abc import Iterator
from dataclasses import dataclass

from infrastructure.ports.external.privacy_shield_port import (
    PrivacyShieldMessageStreamRequest, PrivacyShieldPort,
    PrivacyShieldStreamChunk, PrivacyShieldStreamCompleted,
    PrivacyShieldStreamEvent, PrivacyShieldStreamRequest)


@dataclass(frozen=True)
class FakePrivacyShieldClient(PrivacyShieldPort):
    """Return a safe response stream without calling privacy-shield yet.

    This adapter keeps the web-ui streaming flow ready while the real
    privacy-shield integration and ChatGPT gateway are still pending.

    Attributes:
        chunks (tuple[str, ...]): The safe text chunks emitted by the fake
            privacy-shield stream.
        delay_seconds (float): The delay between fake chunks, used to make the
            streaming behavior visible in the UI.
    """

    chunks: tuple[str, ...] = (
        "He revisado ",
        "el documento procesado. ",
        "La entidad debe ",
        "subsanar la documentacion indicada ",
        "y aportar ",
        "los certificados pendientes. ",
        "Esta es una respuesta ",
        "de prueba generada ",
        "por privacy-shield.",
    )
    message_chunks: tuple[str, ...] = (
        "Respuesta de prueba ",
        "generada en streaming ",
        "para el mensaje escrito. ",
        "Cuando la IA este conectada, ",
        "estos fragmentos llegaran desde el modelo.",
    )
    delay_seconds: float = 0.05

    def stream_safe_response(
        self,
        request: PrivacyShieldStreamRequest,
    ) -> Iterator[PrivacyShieldStreamEvent]:
        """Stream fake safe response events.

        Args:
            request (PrivacyShieldStreamRequest): The chat and document
            identifiers associated with the stream.

        Returns:
            Iterator[PrivacyShieldStreamEvent]: Fake safe chunks and a terminal
            completion event.
        """
        for chunk in self.chunks:
            time.sleep(self.delay_seconds)
            yield PrivacyShieldStreamChunk(event="chunk", content=chunk)

        time.sleep(self.delay_seconds)
        yield PrivacyShieldStreamCompleted(event="completed")

    def stream_message_response(
        self,
        request: PrivacyShieldMessageStreamRequest,
    ) -> Iterator[PrivacyShieldStreamEvent]:
        """Stream fake safe response events for a user message.

        Args:
            request (PrivacyShieldMessageStreamRequest): The chat and message
            associated with the stream.

        Returns:
            Iterator[PrivacyShieldStreamEvent]: Fake safe chunks and a terminal
            completion event.
        """
        for chunk in self.message_chunks:
            time.sleep(self.delay_seconds)
            yield PrivacyShieldStreamChunk(event="chunk", content=chunk)

        time.sleep(self.delay_seconds)
        yield PrivacyShieldStreamCompleted(event="completed")
