"""Domain exceptions used by ai-gateway provider adapters."""
from __future__ import annotations


class ProviderError(Exception):
    """Base exception for upstream language model provider failures."""

    def __init__(self, message: str) -> None:
        """Initialize the provider error.

        Args:
            message (str): The provider failure detail.
        """
        super().__init__(message)


class ProviderRateLimitError(ProviderError):
    """Raised when the upstream provider rejects a request due to rate limits."""


class ProviderConnectionError(ProviderError):
    """Raised when the upstream provider cannot be reached."""


class ProviderAPIError(ProviderError):
    """Raised when the upstream provider returns an API-level failure."""
