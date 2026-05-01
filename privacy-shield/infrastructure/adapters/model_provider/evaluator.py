"""Privacy evaluator backed by the model-provider service."""
from __future__ import annotations

from dataclasses import dataclass

from infrastructure.adapters.model_provider.client import ModelProviderClient
from infrastructure.ports.anonymization_evaluator import AnonymizationEvaluator
from resources.prompts import EVALUATOR_SYSTEM_PROMPT
from utils.json_utils import extract_json_safely


@dataclass
class ModelProviderEvaluator(AnonymizationEvaluator):
    """Evaluate whether a text needs anonymization through model-provider.

    Attributes:
        client (ModelProviderClient): The model-provider HTTP client.
        model_name (str): The loaded model name used for evaluation.
    """

    client: ModelProviderClient
    model_name: str
    last_raw_response: str = ""
    last_parsed_response: dict | None = None
    last_decision: bool | None = None

    def evaluate(self, text: str) -> bool:
        """Evaluate the given text to be anonymized or not.

        Args:
            text (str): The text to be evaluated.

        Returns:
            bool: True if the text should be anonymized, False otherwise.
        """
        prompt = (
            f"{EVALUATOR_SYSTEM_PROMPT}\n\n"
            "Analiza el siguiente contenido y determina si requiere "
            f"anonimizacion:\n\n{text}"
        )
        generated_text = self.client.generate_response(
            model_name=self.model_name,
            prompt=prompt,
        )
        result_json = extract_json_safely(generated_text)
        should_anonymize = bool(
            result_json.get("necesita_anonimizacion", False)
        )
        self.last_raw_response = generated_text
        self.last_parsed_response = result_json
        self.last_decision = should_anonymize
        print(
            "PRIVACY-SHIELD model-provider evaluator "
            f"raw={generated_text!r} "
            f"json={result_json} "
            f"should_anonymize={should_anonymize}",
            flush=True,
        )
        return should_anonymize
