"""
Defines an adapter for anonymizing text using an external language model API.
It sends text to a model provider to identify sensitive information and then redacts it using local utility functions.
"""

import httpx

from infrastructure.ports.anonymizer import Anonymizer
from resources.prompts import (
    build_standard_anonymization_system_prompt,
    should_anonymize_anything,
)
from utils.anonymization_utils import redact_text
from utils.json_utils import extract_json_safely


class ApiAnonymizer(Anonymizer):
    def __init__(self, api_url: str, model_name: str, client: httpx.AsyncClient = None):
        self.api_url = api_url
        self.model_name = model_name
        self.client = client or httpx.AsyncClient()
        self.last_replacements: dict[str, str] = {}

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
            return {"anonymized_text": text, "replacements": {}}

        body = {
            "model_name": self.model_name,
            "system_prompt": build_standard_anonymization_system_prompt(
                settings,
            ),
            "prompt": f"Extrae los datos sensibles del siguiente texto:\n\n{text}"
        }

        response = await self.client.post(self.api_url, json=body, timeout=None)
        response.raise_for_status()

        result_data = response.json()
        generated_text = result_data if isinstance(result_data, str) else result_data.get("response", "")

        extracted_entities = extract_json_safely(generated_text)

        anonymized_text, mapping = redact_text(text, extracted_entities)

        return {"anonymized_text": anonymized_text, "replacements": mapping}
