"""HTTP client used by orchestrator to call privacy-shield."""
from __future__ import annotations

import logging
import os
import uuid
from collections.abc import AsyncIterator
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


LOGGER = logging.getLogger(__name__)


class PrivacyShieldClientError(ExternalServiceClientError):
    """Represent a privacy-shield communication failure."""


@dataclass(frozen=True)
class HttpPrivacyShieldClient(ExternalHttpClientBase, PrivacyShieldPort):
    """Call privacy-shield HTTP endpoints from orchestrator."""

    base_url: str = os.getenv(
        "PRIVACY_SHIELD_BASE_URL",
        "http://127.0.0.1:8002",
    )

    async def anonymize(
        self,
        chat_id: str,
        text: str,
        settings: dict[str, str] | None = None,
    ) -> AnonymizedPrompt:
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
            "settings": settings or {},
        }
        response = await self._post_json("/anonymize/optimized", payload)

        if isinstance(response, str):
            return AnonymizedPrompt(
                text=response,
                replacements={},
                anonymization_id=str(uuid.uuid4()),
                replacement_count=0,
            )

        if not isinstance(response, dict):
            raise PrivacyShieldClientError(
                "Invalid privacy-shield anonymization response."
            )

        replacements = response.get("replacements", {})
        if not isinstance(replacements, dict):
            replacements = {}

        anonymization_id = str(uuid.uuid4())
        normalized_replacements = {
            str(key): str(value)
            for key, value in replacements.items()
        }
        anonymized_text, normalized_replacements = (
            self._namespace_replacements(
                anonymized_text=str(response.get("anonymized_text", "")),
                replacements=normalized_replacements,
                anonymization_id=anonymization_id,
            )
        )

        return AnonymizedPrompt(
            text=anonymized_text,
            replacements=normalized_replacements,
            anonymization_id=anonymization_id,
            replacement_count=len(normalized_replacements),
        )

    async def deanonymize_stream(
        self,
        chunks: AsyncIterator[str],
        replacements: dict[str, str],
    ) -> AsyncIterator[dict[str, Any]]:
        """Stream restored chunks through privacy-shield.

        Args:
            chunks (AsyncIterator[str]): The anonymized assistant response
                chunks.
            replacements (dict[str, str]): Placeholder replacement mappings.

        Returns:
            AsyncIterator[dict[str, Any]]: NDJSON events emitted by privacy-shield.
        """
        session_id = str(uuid.uuid4())
        flush_required = False

        await self._post_json(
            "/deanonymize/session/start",
            {
                "session_id": session_id,
                "replacements": replacements,
            },
        )
        flush_required = True

        try:
            async for chunk in chunks:
                response = await self._post_json(
                    "/deanonymize/session/chunk",
                    {
                        "session_id": session_id,
                        "chunk": chunk,
                    }
                )
                restored_content = str(response.get("content", ""))
                if restored_content:
                    yield {
                        "event": "chunk",
                        "content": restored_content,
                    }
        finally:
            if flush_required:
                try:
                    response = await self._post_json(
                        "/deanonymize/session/flush",
                        {"session_id": session_id},
                    )
                except PrivacyShieldClientError as error:
                    LOGGER.warning(
                        "Could not flush privacy-shield deanonymization session "
                        "%s: %s",
                        session_id,
                        error,
                    )
                else:
                    restored_tail = str(response.get("content", ""))
                    if restored_tail:
                        yield {
                            "event": "chunk",
                            "content": restored_tail,
                        }
            yield {"event": "completed"}

    async def _post_json(self, path: str, payload: dict[str, Any]) -> Any:
        """Send JSON and parse a JSON response.

        Args:
            path (str): The relative API path.
            payload (dict[str, Any]): The request payload.

        Returns:
            Any: The parsed JSON response.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    f"{self.base_url}{path}",
                    json=payload,
                )
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

    def _namespace_replacements(
        self,
        anonymized_text: str,
        replacements: dict[str, str],
        anonymization_id: str,
    ) -> tuple[str, dict[str, str]]:
        """Make placeholders unique for one anonymization session.

        Args:
            anonymized_text (str): The text returned by privacy-shield.
            replacements (dict[str, str]): The original replacement mapping.
            anonymization_id (str): The generated anonymization identifier.

        Returns:
            tuple[str, dict[str, str]]: The namespaced text and mappings.
        """
        namespace = anonymization_id.replace("-", "")[:8].upper()
        namespaced_text = anonymized_text
        namespaced_replacements: dict[str, str] = {}

        for placeholder, original_value in replacements.items():
            namespaced_placeholder = self._build_namespaced_placeholder(
                placeholder,
                namespace,
            )
            namespaced_text = namespaced_text.replace(
                placeholder,
                namespaced_placeholder,
            )
            namespaced_replacements[namespaced_placeholder] = original_value

        return namespaced_text, namespaced_replacements

    def _build_namespaced_placeholder(
        self,
        placeholder: str,
        namespace: str,
    ) -> str:
        """Build a unique placeholder while preserving bracket syntax.

        Args:
            placeholder (str): The placeholder returned by privacy-shield.
            namespace (str): The anonymization namespace.

        Returns:
            str: A placeholder unique for this anonymization.
        """
        if placeholder.startswith("[") and placeholder.endswith("]"):
            return f"[{namespace}_{placeholder[1:-1]}]"

        return f"[{namespace}_{placeholder}]"
