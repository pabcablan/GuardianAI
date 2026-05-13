"""Helpers for masking sensitive entities in extracted text."""
from __future__ import annotations

import re


_ROLE_LINE_PATTERN = re.compile(
    r"^(Presidencia|Vicepresidencia|Secretar[ií]a|Tesorer[ií]a|Vocal(?:\s+\d+)?)$",
    re.IGNORECASE,
)
_DOCUMENT_LINE_PATTERN = re.compile(
    r"^[A-ZXYZ]\d{7,8}[A-Z0-9]$|^[ABCDEFGHJKLMNPQRSUVW]\d{7,8}$",
    re.IGNORECASE,
)
_DATE_LINE_PATTERN = re.compile(r"^\d{2}/\d{2}/\d{4}$")


def redact_text(original_text: str, entities_json: dict) -> tuple[str, dict]:
    """Replace sensitive entities with category placeholders.

    Args:
        original_text (str): The source text that should be anonymized.
        entities_json (dict): The entity payload grouped by category.

    Returns:
        tuple[str, dict]: The anonymized text and placeholder mapping.
    """
    enriched_entities = _augment_entities(original_text, entities_json)
    sorted_entities = _get_sorted_entities(enriched_entities)
    return _apply_masks(original_text, sorted_entities)


def _augment_entities(original_text: str, entities_json: dict) -> dict:
    """Add reconstructed entities that are easy to miss in table layouts."""
    normalized_entities = {
        category: list(values)
        for category, values in entities_json.items()
        if isinstance(values, list)
    }

    reconstructed_names = _extract_table_names(original_text)
    if reconstructed_names:
        existing_names = {
            _normalize_entity_value(value)
            for value in normalized_entities.get("NOMBRE", [])
        }
        normalized_entities.setdefault("NOMBRE", [])
        for name in reconstructed_names:
            if _normalize_entity_value(name) not in existing_names:
                normalized_entities["NOMBRE"].append(name)
                existing_names.add(_normalize_entity_value(name))

    return normalized_entities


def _extract_table_names(text: str) -> list[str]:
    """Reconstruct full names split across multiline table rows."""
    lines = [line.strip() for line in text.splitlines()]
    reconstructed: list[str] = []

    for index, line in enumerate(lines):
        if not line or not _ROLE_LINE_PATTERN.fullmatch(line):
            continue

        row_values: list[str] = []
        cursor = index + 1
        while cursor < len(lines):
            candidate = lines[cursor].strip()
            if not candidate:
                cursor += 1
                continue
            if _ROLE_LINE_PATTERN.fullmatch(candidate):
                break
            row_values.append(candidate)
            if _DOCUMENT_LINE_PATTERN.fullmatch(candidate):
                break
            cursor += 1

        name_parts: list[str] = []
        for candidate in row_values:
            if (
                _DOCUMENT_LINE_PATTERN.fullmatch(candidate)
                or _DATE_LINE_PATTERN.fullmatch(candidate)
            ):
                break
            if candidate in {
                "Cargo",
                "Nombre",
                "Primer Apellido",
                "Segundo Apellido",
                "DNI",
                "Fecha Alta",
                "Fecha Baja",
            }:
                continue
            name_parts.append(candidate)

        if len(name_parts) >= 2:
            reconstructed.append(" ".join(name_parts))

    return reconstructed


def _get_sorted_entities(entities_json: dict) -> list[tuple[str, str]]:
    """Flatten and sort entities so longer matches win first."""
    flat_entities: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for category, values in entities_json.items():
        if not isinstance(values, list):
            continue

        for value in values:
            normalized_value = _normalize_entity_value(str(value))
            if len(normalized_value) <= 2:
                continue

            entity = (normalized_value, category)
            if entity in seen:
                continue

            flat_entities.append(entity)
            seen.add(entity)

    return sorted(flat_entities, key=lambda entity: len(entity[0]), reverse=True)


def _apply_masks(text: str, sorted_entities: list[tuple[str, str]]) -> tuple[str, dict]:
    """Apply placeholders over the text using whitespace-tolerant patterns."""
    mapping: dict[str, str] = {}
    anonymized_text = text
    counters: dict[str, int] = {}
    seen_originals: set[str] = set()

    for original_value, category in sorted_entities:
        normalized_original = _normalize_entity_value(original_value)
        if normalized_original in seen_originals:
            continue

        pattern = _build_entity_pattern(normalized_original)
        if not pattern.search(anonymized_text):
            continue

        counters[category] = counters.get(category, 0) + 1
        label = f"[{category}_{counters[category]}]"

        anonymized_text = pattern.sub(label, anonymized_text)
        mapping[label] = normalized_original
        seen_originals.add(normalized_original)

    return anonymized_text, mapping


def _build_entity_pattern(value: str) -> re.Pattern[str]:
    """Compile a regex that tolerates spaces and newlines between tokens."""
    tokens = [token for token in re.split(r"\s+", value.strip()) if token]
    escaped_tokens = [re.escape(token) for token in tokens]
    pattern = r"\s+".join(escaped_tokens)
    return re.compile(pattern, re.IGNORECASE)


def _normalize_entity_value(value: str) -> str:
    """Normalize whitespace while preserving the visible token content."""
    return " ".join(value.split())
