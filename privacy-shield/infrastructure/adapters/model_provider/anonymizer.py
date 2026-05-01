"""Anonymizer backed by the model-provider service."""
from __future__ import annotations

import re
from dataclasses import dataclass

from infrastructure.adapters.model_provider.client import ModelProviderClient
from infrastructure.ports.anonymizer import Anonymizer
from resources.prompts import ANONYMIZATION_SYSTEM_PROMPT
from utils.json_utils import extract_json_safely


@dataclass
class ModelProviderAnonymizer(Anonymizer):
    """Extract sensitive entities through model-provider and redact them.

    Attributes:
        client (ModelProviderClient): The model-provider HTTP client.
        model_name (str): The loaded model name used for anonymization.
    """

    client: ModelProviderClient
    model_name: str
    last_raw_response: str = ""
    last_parsed_response: dict | None = None
    last_entities: list[tuple[str, str]] | None = None

    def anonymize(self, text: str) -> tuple[str, dict[str, str]]:
        """Anonymize the input text using model-provider inference.

        Args:
            text (str): The input text to be anonymized.

        Returns:
            tuple[str, dict[str, str]]: The anonymized text and replacement map.
        """
        prompt = (
            f"{ANONYMIZATION_SYSTEM_PROMPT}\n\n"
            "Extrae los datos sensibles del siguiente texto:\n\n"
            f"{text}"
        )
        generated_text = self.client.generate_response(
            model_name=self.model_name,
            prompt=prompt,
        )
        extracted_entities = extract_json_safely(generated_text)
        sorted_entities = self._get_sorted_entities(extracted_entities)
        anonymized_text, mapping = self._apply_masks(text, sorted_entities)
        self.last_raw_response = generated_text
        self.last_parsed_response = extracted_entities
        self.last_entities = sorted_entities
        print(
            "PRIVACY-SHIELD model-provider anonymizer "
            f"raw={generated_text!r} "
            f"json={extracted_entities} "
            f"entities={sorted_entities} "
            f"replacement_count={len(mapping)}",
            flush=True,
        )
        return anonymized_text, mapping

    def _get_sorted_entities(self, entities_json: dict) -> list[tuple[str, str]]:
        """Sort extracted entities by descending length.

        Args:
            entities_json (dict): The extracted entities by category.

        Returns:
            list[tuple[str, str]]: Entity values paired with their categories.
        """
        flat_entities = []
        for category, values in entities_json.items():
            if isinstance(values, list):
                for value in values:
                    if len(str(value).strip()) > 2:
                        flat_entities.append((str(value), category))

        return sorted(flat_entities, key=lambda item: len(item[0]), reverse=True)

    def _apply_masks(
        self,
        text: str,
        sorted_entities: list[tuple[str, str]],
    ) -> tuple[str, dict[str, str]]:
        """Replace sensitive entities with placeholders.

        Args:
            text (str): The original text.
            sorted_entities (list[tuple[str, str]]): Entities to redact.

        Returns:
            tuple[str, dict[str, str]]: The anonymized text and replacement map.
        """
        mapping = {}
        anonymized_text = text
        counters = {}

        for original_value, category in sorted_entities:
            if original_value in mapping.values():
                continue

            counters[category] = counters.get(category, 0) + 1
            label = f"[{category}_{counters[category]}]"
            mapping[label] = original_value

            pattern = re.compile(re.escape(original_value), re.IGNORECASE)
            anonymized_text = pattern.sub(label, anonymized_text)

        return anonymized_text, mapping
