"""HTTP error helpers for the orchestrator API."""
from __future__ import annotations

from fastapi import HTTPException, status


def processed_document_not_found() -> HTTPException:
    """Build the processed-document-not-found HTTP error.

    Returns:
        HTTPException: The HTTP 404 error.
    """
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Processed document not found.",
    )


def bad_gateway(error: Exception) -> HTTPException:
    """Build a bad gateway error for downstream service failures.

    Args:
        error (Exception): The downstream service error.

    Returns:
        HTTPException: The HTTP 502 error.
    """
    return HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=str(error),
    )
