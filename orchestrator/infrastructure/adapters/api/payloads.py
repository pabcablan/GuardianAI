"""Payload builders for orchestrator API responses."""
from __future__ import annotations

from typing import Any

from infrastructure.ports.privacy_shield_port import AnonymizedPrompt


def build_anonymized_prompt_event(
    anonymized_prompt: AnonymizedPrompt,
) -> dict[str, Any]:
    """Build the stream event that exposes anonymized text to web-ui.

    Args:
        anonymized_prompt (AnonymizedPrompt): The anonymized prompt metadata.

    Returns:
        dict[str, str]: The stream event payload.
    """
    return {
        "event": "anonymized_prompt",
        "content": anonymized_prompt.text,
        "replacements": anonymized_prompt.replacements,
    }


def build_anonymized_preview_payload(
    anonymized_prompt: AnonymizedPrompt,
    extraction_method: str | None = None,
    original_text: str | None = None,
) -> dict[str, Any]:
    """Build the API payload for anonymization previews.

    Args:
        anonymized_prompt (AnonymizedPrompt): The anonymized prompt metadata.

    Returns:
        dict[str, Any]: The preview payload.
    """
    return {
        "anonymized_text": anonymized_prompt.text,
        "anonymization_id": anonymized_prompt.anonymization_id,
        "replacement_count": anonymized_prompt.replacement_count,
        "extraction_method": extraction_method,
        "replacements": anonymized_prompt.replacements,
        "original_text": original_text,
    }
