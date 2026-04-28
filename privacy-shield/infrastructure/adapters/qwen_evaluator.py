"""
Defines an adapter for the Qwen model to be used as an anonymization evaluator.
It is responsible for evaluating whether a given text contains sensitive information that should be anonymized, using the Qwen model to analyze the content and return a JSON response indicating the evaluation result.
"""

import torch

from infrastructure.ports.anonymization_evaluator import AnonymizationEvaluator
from resources.prompts import EVALUATOR_SYSTEM_PROMPT
from utils.json_utils import extract_json_safely


class QwenEvaluator(AnonymizationEvaluator):

    def __init__(self, model, tokenizer):
        self.model = model
        self.tokenizer = tokenizer
        self.system_prompt = EVALUATOR_SYSTEM_PROMPT
    
    def evaluate(self, text: str) -> bool:
        """
        Evaluate the given text to be anonymized or not because it contains sensitive information.

        Args:
            text (str): The text to be evaluated.
        
        Returns:
            bool: True if the text should be anonymized, False otherwise.
        """
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user",
             "content": f"Analiza el siguiente contenido y determina si requiere anonimización:\n\n{text}"}
        ]

        input_text = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.tokenizer(text=input_text, return_tensors="pt").to(self.model.device)

        with torch.no_grad():
            output_ids = self.model.generate(**inputs, max_new_tokens=600, temperature=0.01, do_sample=False,
                                             repetition_penalty=1.1)

        input_tokens_len = inputs["input_ids"].shape[1]
        generated_tokens = output_ids[0][input_tokens_len:]
        decoded_text = self.tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()
        result_json = extract_json_safely(decoded_text)

        return result_json