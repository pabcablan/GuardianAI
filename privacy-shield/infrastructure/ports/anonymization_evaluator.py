"""
Defines the contract for the anonymization evaluator. 
It is responsible for evaluating whether a given text contains sensitive information that should be anonymized.
"""

from abc import ABC, abstractmethod

class AnonymizationEvaluator(ABC):
    @abstractmethod
    async def evaluate(self, text: str) -> bool:
        """
        Evaluate the given text to be anonymized or not becausa it contains sensitive information.
        
        Args:
            text (str): The text to be evaluated.

        Returns:
            bool: True if the text should be anonymized, False otherwise.
        """
        pass