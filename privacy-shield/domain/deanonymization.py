"""Domain models and rules for restoring anonymized placeholders."""
from __future__ import annotations

import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping


PLACEHOLDER_PATTERN = re.compile(r"\[[A-Z]+_\d+\]")


@dataclass(frozen=True)
class Replacement:
    """Represent one restored placeholder occurrence.

    Attributes:
        placeholder (str): The anonymized token found in the text.
        value (str): The original value used to replace the token.
        occurrences (int): The number of replacements applied.
    """

    placeholder: str
    value: str
    occurrences: int


@dataclass(frozen=True)
class DeanonymizationMap:
    """Represent the mapping between placeholders and original values.

    Attributes:
        values (Mapping[str, str]): The immutable placeholder-to-value mapping.
    """

    values: Mapping[str, str]

    def __post_init__(self) -> None:
        """Validate and freeze the placeholder mapping.

        Raises:
            ValueError: If a placeholder or replacement value is invalid.
        """
        normalized_values: dict[str, str] = {}
        for placeholder, value in self.values.items():
            if not PLACEHOLDER_PATTERN.fullmatch(placeholder):
                raise ValueError(f"Invalid placeholder: {placeholder}")
            if not isinstance(value, str) or value == "":
                raise ValueError(f"Invalid replacement for {placeholder}")
            normalized_values[placeholder] = value

        object.__setattr__(
            self,
            "values",
            MappingProxyType(normalized_values),
        )

    def restore(self, text: str) -> tuple[str, list[Replacement]]:
        """Restore every known placeholder found in the text.

        Args:
            text (str): The text that contains anonymized placeholders.

        Returns:
            tuple[str, list[Replacement]]: The restored text and replacement
            details.
        """
        restored_text = text
        replacements: list[Replacement] = []

        for placeholder, value in self.values.items():
            occurrences = restored_text.count(placeholder)
            if occurrences == 0:
                continue

            restored_text = restored_text.replace(placeholder, value)
            replacements.append(
                Replacement(
                    placeholder=placeholder,
                    value=value,
                    occurrences=occurrences,
                )
            )

        return restored_text, replacements

    def find_unknown_placeholders(self, text: str) -> list[str]:
        """Find placeholders that are present in text but absent from the map.

        Args:
            text (str): The text to inspect.

        Returns:
            list[str]: The sorted unknown placeholders.
        """
        placeholders = set(PLACEHOLDER_PATTERN.findall(text))
        unknown_placeholders = placeholders.difference(self.values.keys())
        return sorted(unknown_placeholders)

    def find_unused_placeholders(self, text: str) -> list[str]:
        """Find mapped placeholders that are not present in text.

        Args:
            text (str): The text to inspect.

        Returns:
            list[str]: The sorted unused placeholders.
        """
        placeholders = set(PLACEHOLDER_PATTERN.findall(text))
        unused_placeholders = set(self.values.keys()).difference(placeholders)
        return sorted(unused_placeholders)
