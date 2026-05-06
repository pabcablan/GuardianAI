"""HTTP client used by orchestrator to call privacy-shield."""
from __future__ import annotations

import json
import os
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

import httpx

from infrastructure.adapters.http.base import (
    ExternalHttpClientBase,
    ExternalServiceClientError,
)
from infrastructure.ports.privacy_shield_port import (
    AnonymizedPrompt,
    PrivacyShieldPort,
)


class PrivacyShieldClientError(ExternalServiceClientError):
    """Represent a privacy-shield communication failure."""


@dataclass(frozen=True)
class HttpPrivacyShieldClient(ExternalHttpClientBase, PrivacyShieldPort):
    """Call privacy-shield HTTP endpoints from orchestrator."""

    base_url: str = os.getenv(
        "PRIVACY_SHIELD_BASE_URL",
        "http://127.0.0.1:8002",
    )

    def anonymize(self, chat_id: str, text: str) -> AnonymizedPrompt:
        """Anonymize text through privacy-shield.

        Args:
            chat_id (str): The chat that owns the prompt.
            text (str): The original prompt.

        Returns:
            AnonymizedPrompt: The anonymized text and replacement map.
        """
        payload = {
            "chat_id": chat_id,
            "text": text,
        }
        response = self._post_json("/anonymize", payload)
        replacements = response.get("replacements", {})
        if not isinstance(replacements, dict):
            replacements = {}

        return AnonymizedPrompt(
            text=str(response.get("anonymized_text", "")),
            replacements={
                str(key): str(value)
                for key, value in replacements.items()
            },
            anonymization_id=str(response["anonymization_id"]),
            replacement_count=int(response.get("replacement_count", 0)),
        )

    def deanonymize_stream(
        self,
        chunks: list[str],
        replacements: dict[str, str],
    ) -> Iterator[dict[str, Any]]:
        """Stream deanonymized chunks through privacy-shield.

        Args:
            chunks (list[str]): The anonymized assistant response chunks.
            replacements (dict[str, str]): The replacements for
                deanonymization.

        Returns:
            Iterator[dict[str, Any]]: NDJSON events emitted by privacy-shield.
        """
        payload = {
            "chunks": chunks,
            "replacements": replacements,
        }

        try:
            with httpx.stream(
                "POST",
                f"{self.base_url}/deanonymize/stream",
                json=payload,
                timeout=self.timeout_seconds,
            ) as response:
                self._raise_for_status(
                    response=response,
                    service_name="Privacy-shield",
                    error_type=PrivacyShieldClientError,
                    read_stream=True,
                )
                for line in response.iter_lines():
                    if not line:
                        continue
                    yield json.loads(line)
        except httpx.RequestError as error:
            raise PrivacyShieldClientError(
                "Privacy-shield service is unavailable."
            ) from error

    def _post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Send JSON and parse a JSON response.

        Args:
            path (str): The relative API path.
            payload (dict[str, Any]): The request payload.

        Returns:
            dict[str, Any]: The parsed JSON response.
        """
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(f"{self.base_url}{path}", json=payload)
                self._raise_for_status(
                    response=response,
                    service_name="Privacy-shield",
                    error_type=PrivacyShieldClientError,
                )
                return response.json()
        except httpx.RequestError as error:
            raise PrivacyShieldClientError(
                "Privacy-shield service is unavailable."
            ) from error
