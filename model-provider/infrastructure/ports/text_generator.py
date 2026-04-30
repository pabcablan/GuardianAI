from abc import ABC, abstractmethod
from typing import Any

class TextGenerator(ABC):
    @abstractmethod
    def generate(self, prompt: str, model: Any, tokenizer: Any) -> str:
        """
        Generates a response based on the given prompt.

        Args:
            prompt (str): The input prompt to generate a response for.
            model (Any): The model to use for generation.
            tokenizer (Any): The tokenizer to use for generation.
        """
        pass    