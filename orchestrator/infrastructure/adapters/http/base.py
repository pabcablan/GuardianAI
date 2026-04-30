"""Shared utilities for orchestrator HTTP adapters."""
from __future__ import annotations

from dataclasses import dataclass

import httpx


class ExternalServiceClientError(RuntimeError):
    """Represent a failure when consuming an external service."""


@dataclass(frozen=True)
class ExternalHttpClientBase:
    """Provide shared timeout and status handling for HTTP adapters.

    Attributes:
        base_url (str): The external service base URL.
        timeout_seconds (float): The request timeout in seconds.
    """

    base_url: str
    timeout_seconds: float = 600.0

    def _raise_for_status(
        self,
        response: httpx.Response,
        service_name: str,
        error_type: type[ExternalServiceClientError],
        read_stream: bool = False,
    ) -> None:
        """Raise a domain error when an external service returns an HTTP error.

        Args:
            response (httpx.Response): The HTTP response to validate.
            service_name (str): The name used in error messages.
            error_type (type[ExternalServiceClientError]): The error class to
                raise.
            read_stream (bool): Whether the response body must be read before
                accessing its text.

        Raises:
            ExternalServiceClientError: If the response has an error status.
        """
        if response.is_success:
            return

        if read_stream:
            response.read()

        raise error_type(
            f"{service_name} request failed with status "
            f"{response.status_code}: "
            f"{response.text or 'No error detail returned.'}"
        )
