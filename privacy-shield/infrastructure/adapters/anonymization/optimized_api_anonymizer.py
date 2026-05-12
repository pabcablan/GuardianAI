"""
Defines an adapter for anonymizing text using an external language model API.
It sends text to a model provider to identify sensitive information and then redacts it using local utility functions.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import httpx

from infrastructure.ports.anonymizer import Anonymizer
from resources.prompts import (
    build_optimized_anonymization_system_prompt,
    should_anonymize_anything,
)
from utils.anonymization_utils import redact_text
from utils.json_utils import extract_json_safely


class OptimizedApiAnonymizer(Anonymizer):
    def __init__(self, api_url: str, model_name: str, client: httpx.AsyncClient = None):
        self.api_url = api_url
        self.model_name = model_name
        self.client = client or httpx.AsyncClient()
        self._debug_path = (
            Path(__file__).resolve().parents[3]
            / "storage"
            / "anonymization_debug.jsonl"
        )

    async def anonymize(
        self,
        text: str,
        settings: dict[str, str] | None = None,
    ) -> dict:
        """
        Anonymizes the input text by sending it to an external API for processing and then redacting the sensitive information based on the API response.

        Args:
            text (str): The input text to be anonymized.

        Returns:
            dict: The anonymized version of the input text with the anonymized fields.
        """
        if not should_anonymize_anything(settings):
            self._write_debug_entry(
                text=text,
                settings=settings,
                generated_text="",
                parsed_data={},
                entities={},
                mapping={},
                skipped_reason="all_categories_disabled",
            )
            return {"anonymized_text": text, "replacements": {}}

        body = {
            "model_name": self.model_name,
            "system_prompt": build_optimized_anonymization_system_prompt(
                settings,
            ),
            "prompt": f"Extrae los datos sensibles del siguiente texto:\n\n{text}"
        }

        response = await self.client.post(self.api_url, json=body, timeout=None)
        response.raise_for_status()

        result_data = response.json()
        generated_text = result_data if isinstance(result_data, str) else result_data.get("response", "")

        data = extract_json_safely(generated_text)
        
        if not data:
            self._write_debug_entry(
                text=text,
                settings=settings,
                generated_text=generated_text,
                parsed_data={},
                entities={},
                mapping={},
                skipped_reason="json_parse_failed_or_truncated",
            )
            return {"anonymized_text": text, "replacements": {}}

        if not data.get("necesita_anonimizacion", False):
            self._write_debug_entry(
                text=text,
                settings=settings,
                generated_text=generated_text,
                parsed_data=data,
                entities={},
                mapping={},
                skipped_reason="model_returned_false",
            )
            return {"anonymized_text": text, "replacements": {}}

        entities = data.get("entidades", {})
        anonymized_text, mapping = redact_text(text, entities)
        self._write_debug_entry(
            text=text,
            settings=settings,
            generated_text=generated_text,
            parsed_data=data,
            entities=entities if isinstance(entities, dict) else {},
            mapping=mapping,
            skipped_reason=None,
        )

        return {"anonymized_text": anonymized_text, "replacements": mapping}

    def _write_debug_entry(
        self,
        text: str,
        settings: dict[str, str] | None,
        generated_text: str,
        parsed_data: dict,
        entities: dict,
        mapping: dict[str, str],
        skipped_reason: str | None,
    ) -> None:
        try:
            self._debug_path.parent.mkdir(parents=True, exist_ok=True)
            entry = {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "model_name": self.model_name,
                "settings": settings or {},
                "text": text,
                "skipped_reason": skipped_reason,
                "raw_response": generated_text,
                "parsed_response": parsed_data,
                "entities": entities,
                "replacement_keys": list(mapping.keys()),
                "replacement_count": len(mapping),
            }
            with self._debug_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            pass
