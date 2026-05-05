"""
Defines an adapter for evaluating text using an external language model API.
It sends text to a model provider to determine if it contains sensitive information that requires anonymization, and returns a boolean result based on the API response.
"""

import httpx

from infrastructure.ports.anonymization_evaluator import AnonymizationEvaluator
from resources.prompts import EVALUATOR_SYSTEM_PROMPT
from utils.json_utils import extract_json_safely


class ApiEvaluator(AnonymizationEvaluator):

    def __init__(self, api_url: str, model_name: str, client: httpx.AsyncClient = None):
        self.api_url = api_url
        self.model_name = model_name
        self.system_prompt = EVALUATOR_SYSTEM_PROMPT
        self.client = client or httpx.AsyncClient()

    async def evaluate(self, text: str) -> bool:
        """
        Evaluate the given text to be anonymized or not because it contains sensitive information.

        Args:
            text (str): The text to be evaluated.

        Returns:
            bool: True if the text should be anonymized, False otherwise.
        """
        body =  {
            "model_name": self.model_name,
            "system_prompt": self.system_prompt,
            "prompt": f"Analiza el siguiente contenido y determina si requiere anonimización:\n\n{text}"
            }

        response = await self.client.post(self.api_url, json=body, timeout=None)
        response.raise_for_status()

        result_json = extract_json_safely(response.json())
        return result_json.get("necesita_anonimizacion", False)