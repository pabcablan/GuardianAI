"""HTTP client used by the orchestrator to call privacy-shield."""
from __future__ import annotations

import contextlib
import json
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class PrivacyShieldClientError(RuntimeError):
    """Represent a privacy-shield communication failure."""


@dataclass(frozen=True)
class AnonymizedPrompt:
    """Represent a prompt anonymized by privacy-shield.

    Attributes:
        text (str): The anonymized prompt.
        replacements (Mapping[str, str]): The placeholder-to-original map.
    """

    text: str
    replacements: Mapping[str, str]


@dataclass(frozen=True)
class HttpPrivacyShieldClient:
    """Call privacy-shield HTTP endpoints from the orchestrator.

    Attributes:
        base_url (str): The privacy-shield API base URL.
    """

    base_url: str = "http://127.0.0.1:7002"

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
        response = self._post_json("/api/anonymize", payload)
        return AnonymizedPrompt(
            text=str(response["anonymized_text"]),
            replacements=response.get("replacements", {}),
        )

    def deanonymize_stream(
        self,
        chunks: list[str],
        replacements: Mapping[str, str],
    ) -> Iterator[dict[str, Any]]:
        """Stream deanonymized chunks through privacy-shield.

        Args:
            chunks (list[str]): The anonymized assistant response chunks.
            replacements (Mapping[str, str]): The placeholder-to-original map.

        Returns:
            Iterator[dict[str, Any]]: NDJSON events emitted by privacy-shield.
        """
        payload = {
            "chunks": chunks,
            "replacements": dict(replacements),
        }
        request = self._build_request("/api/deanonymize/stream", payload)

        try:
            response = urlopen(request, timeout=600)
        except HTTPError as error:
            detail = self._read_error_detail(error)
            raise PrivacyShieldClientError(
                "Privacy-shield request failed with status "
                f"{error.code}: {detail}"
            ) from error
        except URLError as error:
            raise PrivacyShieldClientError(
                "Privacy-shield service is unavailable."
            ) from error

        with contextlib.closing(response) as stream:
            for raw_line in stream:
                line = raw_line.decode("utf-8").strip()
                if not line:
                    continue
                yield json.loads(line)

    def _post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Send JSON and parse a JSON response.

        Args:
            path (str): The relative API path.
            payload (dict[str, Any]): The request payload.

        Returns:
            dict[str, Any]: The parsed JSON response.
        """
        request = self._build_request(path, payload)

        try:
            response = urlopen(request, timeout=600)
        except HTTPError as error:
            detail = self._read_error_detail(error)
            raise PrivacyShieldClientError(
                "Privacy-shield request failed with status "
                f"{error.code}: {detail}"
            ) from error
        except URLError as error:
            raise PrivacyShieldClientError(
                "Privacy-shield service is unavailable."
            ) from error

        with contextlib.closing(response) as stream:
            return json.loads(stream.read().decode("utf-8"))

    def _build_request(
        self,
        path: str,
        payload: dict[str, Any],
    ) -> Request:
        """Build a JSON POST request.

        Args:
            path (str): The relative API path.
            payload (dict[str, Any]): The request payload.

        Returns:
            Request: The configured HTTP request.
        """
        body = json.dumps(payload).encode("utf-8")
        return Request(
            url=f"{self.base_url}{path}",
            data=body,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Content-Length": str(len(body)),
            },
        )

    def _read_error_detail(self, error: HTTPError) -> str:
        """Read a useful detail from an HTTP error response.

        Args:
            error (HTTPError): The raised HTTP error.

        Returns:
            str: The response body or a fallback message.
        """
        try:
            body = error.read().decode("utf-8").strip()
        except OSError:
            return "No error detail returned."

        return body or "No error detail returned."
