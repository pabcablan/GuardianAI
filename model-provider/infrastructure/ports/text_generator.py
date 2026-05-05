"""Port that defines model text generation."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class TextGenerator(ABC):
    """Define the contract for text generation engines."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        model: Any,
        tokenizer: Any,
        document_base64: str | None = None,
    ) -> str:
        """Generate a response based on a prompt.

        Args:
            prompt (str): The input prompt.
            model (Any): The loaded model.
            tokenizer (Any): The tokenizer or processor.
            document_base64 (str | None): Optional base64 document payload.

        Returns:
            str: The generated response.
        """
        raise NotImplementedError
