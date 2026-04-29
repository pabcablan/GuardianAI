"""
Defines an adapter for anonymizing text using a language model.
It purpose is to use a language model to identify and redact sensitive information from text, replacing it with category-based placeholders.
"""

import re

import torch

from infrastructure.ports.anonymizer import Anonymizer
from resources.prompts import ANONYMIZATION_SYSTEM_PROMPT
from utils.json_utils import extract_json_safely


class LlmAnonymizer(Anonymizer):
    def __init__(self, model, tokenizer):
        self.model = model
        self.tokenizer = tokenizer
        self.system_prompt = ANONYMIZATION_SYSTEM_PROMPT
    
    def anonymize(self, text:str) -> str:
        """
        Anonymizes the input text by extracting sensitive information using a language model and replacing it with placeholders.

        Args:
            text (str): The input text to be anonymized.
        
        Returns:
            str: The anonymized text with sensitive information replaced by placeholders.
        """
        message = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": self.system_prompt + "\n\nExtrae los datos sensibles del siguiente texto:\n\n" + text}
                ]
            }
        ]
        
        input_text = self.tokenizer.apply_chat_template(message, tokenize=False, add_generation_prompt=True)
        inputs = self.tokenizer(text=input_text, return_tensors="pt").to(self.model.device)
        
        with torch.no_grad():
            output_ids = self.model.generate(**inputs, max_new_tokens=600,  temperature=0.01, do_sample=False, repetition_penalty=1.1)

        input_tokens = inputs["input_ids"].shape[1]
        generated_tokens = output_ids[0][input_tokens:]
        generated_text = self.tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()
        extracted_entities = extract_json_safely(generated_text)

        return self._redact_text(text, extracted_entities)

    def _redact_text(self, original_text: str, entities_json: dict) -> tuple[str, dict]:
            """
            Redacts the original text by replacing sensitive information with placeholders based on the extracted entities.

            Args:
                original_text (str): The original text to be redacted.
                entities_json (dict): A dictionary containing the extracted entities categorized by their types.
            
            Returns:
                tuple[str, dict]: A tuple containing the redacted text and a mapping of placeholders to original values.
            """
            sorted_entities = self._get_sorted_entities(entities_json)
            return self._apply_masks(original_text, sorted_entities)

    def _get_sorted_entities(self, entities_json: dict) -> list[tuple]:
        """
        Sorts the extracted entities by their length in descending order to ensure that longer matches are replaced before shorter ones.

        Args:
            entities_json (dict): A dictionary containing the extracted entities categorized by their types.

        Returns:
            list[tuple]: A list of tuples where each tuple contains an entity value and its corresponding category, sorted by the length of the entity value in descending order.
        """
        flat_entities = []
        for category, values in entities_json.items():
            if isinstance(values, list):
                for value in values:
                    if len(str(value).strip()) > 2:
                        flat_entities.append((str(value), category))

        return sorted(flat_entities, key=lambda x: len(x[0]), reverse=True)

    def _apply_masks(self, text: str, sorted_entities: list[tuple]) -> tuple[str, dict]:
        """
        Applies masks to the original text by replacing sensitive information with placeholders.

        Args:
            text (str): The original text to be redacted.
            sorted_entities (list[tuple]): A list of tuples containing the entity values and their corresponding categories, sorted by entity length.

        Returns:
            tuple[str, dict]: A tuple containing the redacted text and a mapping of placeholders to original values.
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