import json
from datetime import datetime, timezone
from pathlib import Path

import httpx

from infrastructure.ports.anonymizer import Anonymizer
from resources.anonymization_prompt_builder import (
    build_optimized_anonymization_system_prompt,
)
from resources.anonymization_settings import should_anonymize_anything
from utils.anonymization_utils import redact_text
from utils.json_utils import extract_json_safely


class OptimizedApiAnonymizer(Anonymizer):
    """Anonymize text through the shared model-provider service."""

    def __init__(
        self,
        api_url: str,
        model_name: str,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        """Initialize the API-backed anonymizer."""
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
    ) -> dict[str, object]:
        """Detect entities through model-provider and redact them locally.

        Args:
            text (str): Source text that may contain sensitive entities.
            settings (dict[str, str] | None): Category-level anonymization modes.

        Returns:
            dict[str, object]: Anonymized text and placeholder replacement map.
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
            return self._build_result(text, {})

        generated_text = await self._request_model_response(text, settings)
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
            return self._build_result(text, {})

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
            return self._build_result(text, {})

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

        return self._build_result(anonymized_text, mapping)

    async def _request_model_response(
        self,
        text: str,
        settings: dict[str, str] | None,
    ) -> str:
        """Send the anonymization request to model-provider.

        Args:
            text (str): Source text sent for entity extraction.
            settings (dict[str, str] | None): Category-level anonymization modes.

        Returns:
            str: Raw text payload returned by model-provider.
        """
        body = {
            "model_name": self.model_name,
            "system_prompt": build_optimized_anonymization_system_prompt(settings),
            "prompt": f"Extrae los datos sensibles del siguiente texto:\n\n{text}",
        }

        response = await self.client.post(self.api_url, json=body, timeout=None)
        response.raise_for_status()

        response_payload = response.json()
        if isinstance(response_payload, str):
            return response_payload

        return response_payload.get("response", "")

    @staticmethod
    def _build_result(
        anonymized_text: str,
        replacements: dict[str, str],
    ) -> dict[str, object]:
        """Build the public anonymization payload.

        Args:
            anonymized_text (str): Text after placeholder replacement.
            replacements (dict[str, str]): Placeholder-to-original mapping.

        Returns:
            dict[str, object]: Response payload exposed by the anonymizer.
        """
        return {
            "anonymized_text": anonymized_text,
            "replacements": replacements,
        }

    def _write_debug_entry(
        self,
        text: str,
        settings: dict[str, str] | None,
        generated_text: str,
        parsed_data: dict[str, object],
        entities: dict[str, object],
        mapping: dict[str, str],
        skipped_reason: str | None,
    ) -> None:
        """Persist a debug trace for anonymization troubleshooting.

        Args:
            text (str): Original text submitted for anonymization.
            settings (dict[str, str] | None): Category-level anonymization modes.
            generated_text (str): Raw model response text.
            parsed_data (dict[str, object]): Parsed JSON payload, if available.
            entities (dict[str, object]): Extracted entities grouped by category.
            mapping (dict[str, str]): Placeholder-to-original replacement map.
            skipped_reason (str | None): Reason why anonymization was skipped.

        Returns:
            None: Writes a debug line when possible and ignores write failures.
        """
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
