"""
Defines an adapter for anonymizing text using a language model.
It purpose is to use a language model to identify and redact sensitive information from text, replacing it with category-based placeholders.
"""

import re

from fastapi.concurrency import run_in_threadpool
import torch

from infrastructure.ports.anonymizer import Anonymizer
from resources.prompts import (
    build_standard_anonymization_system_prompt,
    should_anonymize_anything,
)
from utils.json_utils import extract_json_safely
from utils.anonymization_utils import redact_text

class LlmAnonymizer(Anonymizer):
    def __init__(self, model, tokenizer):
        self.model = model
        self.tokenizer = tokenizer
    
    async def anonymize(
        self,
        text: str,
        settings: dict[str, str] | None = None,
    ) -> dict:
        """
        Anonymizes the input text by extracting sensitive information using a language model and replacing it with placeholders.

        Args:
            text (str): The input text to be anonymized.
        
        Returns:
            dict: The anonymized version of the input text with the anonymized fields.
        """

        if not should_anonymize_anything(settings):
            return {"anonymized_text": text, "replacements": {}}

        return await run_in_threadpool(
            None,
            self._run_anonymization,
            text,
            build_standard_anonymization_system_prompt(settings),
        )
    
    def _run_anonymization(self, text: str, system_prompt: str) -> dict:
        message = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": system_prompt + "\n\nExtrae los datos sensibles del siguiente texto:\n\n" + text}
                ]
            }
        ]

        input_text = self.tokenizer.apply_chat_template(
            message,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
        inputs = self.tokenizer(text=input_text, return_tensors="pt").to(self.model.device)
        
        with torch.no_grad():
            output_ids = self.model.generate(**inputs, max_new_tokens=600,  temperature=0.01, do_sample=False, repetition_penalty=1.1)

        input_tokens = inputs["input_ids"].shape[1]
        generated_tokens = output_ids[0][input_tokens:]
        generated_text = self.tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()
        extracted_entities = extract_json_safely(generated_text)

        anonymized_text, mapping = redact_text(text, extracted_entities)
        return {"anonymized_text": anonymized_text, "replacements": mapping}
