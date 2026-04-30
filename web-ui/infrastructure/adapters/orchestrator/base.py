"""Shared utilities for orchestrator HTTP clients."""
from __future__ import annotations

import json
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
