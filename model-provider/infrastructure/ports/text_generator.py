"""Port for generating text from loaded model runtimes."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class TextGenerator(ABC):
    """Define inference operations over loaded models."""

    @abstractmethod
    def generate(
        self,
        system_prompt: str | None,
        prompt: str,
        model: Any,
        processor: Any,
        document_base64: str | None = None,
    ) -> str:
        """Generate one response from text or document input.

        Args:
            system_prompt (str | None): Optional system instructions that guide
                generation.
            prompt (str): The user prompt or extraction instruction.
            model (Any): The loaded model object used for inference.
            processor (Any): The paired processor or tokenizer object.
            document_base64 (str | None): Optional base64-encoded PDF content
                for document-aware inference.

        Returns:
            str: The generated model response.
        """
        ...
