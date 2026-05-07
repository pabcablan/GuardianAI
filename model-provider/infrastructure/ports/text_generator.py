from abc import ABC, abstractmethod
from typing import Any

class TextGenerator(ABC):
    @abstractmethod
    def generate(self, system_prompt: str, prompt: str, model: Any, processor: Any) -> str:
        """
        Generates a response based on the given prompt.

        Args:
            system_prompt (str): The system prompt to provide context for the generation.
            prompt (str): The input prompt to generate a response for.
            model (Any): The model to use for generation.
            processor (Any): The processor to use for generation.
        """
        pass    