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
_ADDRESS_FIELD_LABEL_PATTERN = re.compile(
    r"^(Calle:\s*\*?|Calle:?|\*|Número:?|Puerta/Piso/Otros:?|Código Postal:?|Población:?|Municipio:?|Provincia:?)$",
    re.IGNORECASE,
)
_ADDRESS_SECTION_HEADER_PATTERN = re.compile(
    r"^Domicilio social:?$",
    re.IGNORECASE,
)


def redact_text(original_text: str, entities_json: dict) -> tuple[str, dict]:
    """Replace sensitive entities with category placeholders.

    Args:
        original_text (str): Source text that should be anonymized.
        entities_json (dict): Entity payload grouped by anonymization category.

    Returns:
        tuple[str, dict]: Anonymized text and placeholder replacement mapping.
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

    reconstructed_addresses = _extract_structured_address_values(original_text)
    if reconstructed_addresses:
        existing_addresses = {
            _normalize_entity_value(value)
            for value in normalized_entities.get("DIR", [])
        }
        normalized_entities.setdefault("DIR", [])
        for address_value in reconstructed_addresses:
            normalized_address = _normalize_entity_value(address_value)
            if normalized_address not in existing_addresses:
                normalized_entities["DIR"].append(address_value)
                existing_addresses.add(normalized_address)

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
            if len(normalized_value) <= 2 and not _should_keep_short_entity(
                normalized_value,
                category,
            ):
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


def _extract_structured_address_values(text: str) -> list[str]:
    """Extract address field values from linealized form sections."""
    lines = [line.strip() for line in text.splitlines()]
    extracted_values: list[str] = []
    inside_address_section = False
    index = 0

    while index < len(lines):
        line = lines[index]
        if not line:
            index += 1
            continue

        if _ADDRESS_SECTION_HEADER_PATTERN.fullmatch(line):
            inside_address_section = True
            index += 1
            continue

        if inside_address_section and line.endswith(":") and not _ADDRESS_FIELD_LABEL_PATTERN.fullmatch(line):
            break

        if inside_address_section and _ADDRESS_FIELD_LABEL_PATTERN.fullmatch(line):
            next_value = _collect_next_field_value(lines, index + 1)
            if next_value:
                extracted_values.append(next_value)

        index += 1

    return extracted_values


def _collect_next_field_value(lines: list[str], start_index: int) -> str | None:
    """Collect the first real value that follows one form field label."""
    cursor = start_index
    collected_parts: list[str] = []

    while cursor < len(lines):
        candidate = lines[cursor].strip()
        if not candidate:
            cursor += 1
            continue

        if _ADDRESS_FIELD_LABEL_PATTERN.fullmatch(candidate):
            break

        if candidate.endswith(":") and not collected_parts:
            break

        if candidate.endswith(":") and collected_parts:
            break

        collected_parts.append(candidate)
        break

    if not collected_parts:
        return None

    return " ".join(collected_parts).strip()


def _should_keep_short_entity(value: str, category: str) -> bool:
    """Allow short address fragments such as house numbers to be anonymized."""
    if category != "DIR":
        return False

    return bool(re.fullmatch(r"[\dA-Z/-]{1,4}", value, re.IGNORECASE))
