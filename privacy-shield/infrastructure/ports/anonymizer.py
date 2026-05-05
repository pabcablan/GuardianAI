"""
Defines the contract for the anonymizer component.
It is responsible for anonymizing text data to protect sensitive information.
"""

from abc import ABC, abstractmethod

class Anonymizer(ABC):
    @abstractmethod
    async def anonymize(self, text:str) -> str:
        """
        Anonymizes the given text and returns the anonymized version.

        Args:
            text (str): The input text to be anonymized.
        
        Returns:
            str: The anonymized version of the input text.
        """
        pass
