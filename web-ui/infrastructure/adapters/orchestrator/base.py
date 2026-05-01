"""Shared utilities for orchestrator HTTP clients."""
from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass

import httpx


class OrchestratorClientError(RuntimeError):
    """Represent a failure when consuming orchestrator HTTP endpoints."""


@dataclass(frozen=True)
class OrchestratorHttpClientBase:
    """Provide common configuration and error handling for orchestrator clients.

    Attributes:
        base_url (str): The base URL of the orchestrator service.
        timeout_seconds (float): The request timeout in seconds.
    """

    base_url: str = "http://127.0.0.1:8003"
    timeout_seconds: float = 600.0

    def _stream_json_lines(
        self,
        path: str,
        payload: dict[str, str],
    ) -> Iterator[str]:
        """POST JSON to orchestrator and yield NDJSON response lines.

        Args:
            path (str): The orchestrator API path.
            payload (dict[str, str]): The JSON request body.

        Yields:
            str: One non-empty NDJSON line.
        """
        try:
            with httpx.stream(
                "POST",
                f"{self.base_url}{path}",
                json=payload,
                timeout=self.timeout_seconds,
            ) as response:
                self._raise_for_status(response)
                yield from self._iter_non_empty_lines(response)
        except httpx.RequestError as error:
            raise OrchestratorClientError(
                "Orchestrator service is unavailable."
            ) from error

    def _stream_form_lines(
        self,
        path: str,
        data: dict[str, str],
        files: dict[str, tuple[str, bytes, str]],
    ) -> Iterator[str]:
        """POST multipart form data and yield NDJSON response lines.

        Args:
            path (str): The orchestrator API path.
            data (dict[str, str]): Form fields sent with the request.
            files (dict[str, tuple[str, bytes, str]]): Uploaded files.

        Yields:
            str: One non-empty NDJSON line.
        """
        try:
            with httpx.stream(
                "POST",
                f"{self.base_url}{path}",
                data=data,
                files=files,
                timeout=self.timeout_seconds,
            ) as response:
                self._raise_for_status(response)
                yield from self._iter_non_empty_lines(response)
        except httpx.RequestError as error:
            raise OrchestratorClientError(
                "Orchestrator service is unavailable."
            ) from error

    def _iter_non_empty_lines(
        self,
        response: httpx.Response,
    ) -> Iterator[str]:
        """Yield non-empty lines from an HTTP stream.

        Args:
            response (httpx.Response): The streaming HTTP response.

        Yields:
            str: One non-empty line from the response body.
        """
        for line in response.iter_lines():
            if not line:
                continue
            yield line

    def _raise_for_status(self, response: httpx.Response) -> None:
        """Raise a domain error when orchestrator returns an HTTP error.

        Args:
            response (httpx.Response): The HTTP response to validate.

        Raises:
            OrchestratorClientError: If the response has an error status.
        """
        if response.is_success:
            return

        response.read()
        detail = response.text or "No error detail returned."
        try:
            payload = response.json()
        except json.JSONDecodeError:
            pass
        else:
            if isinstance(payload, dict):
                detail = str(payload.get("detail", detail))

        raise OrchestratorClientError(
            f"Orchestrator request failed with status "
            f"{response.status_code}: {detail}"
        )
