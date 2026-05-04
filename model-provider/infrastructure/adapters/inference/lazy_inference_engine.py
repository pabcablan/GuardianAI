"""Lazy inference engine adapter for model-provider."""
from __future__ import annotations

from typing import Any

from infrastructure.ports.text_generator import TextGenerator


class LazyModelInferenceEngine(TextGenerator):
    """Import the inference engine only when generation is requested."""

    def __init__(self) -> None:
        """Initialize the lazy inference engine."""
        self._engine = None

    def _get_engine(self):
        """Return the concrete inference engine.

        Returns:
            ModelInferenceEngine: The concrete inference engine.
        """
        if self._engine is None:
            from infrastructure.adapters.inference.model_inference_engine import (
                ModelInferenceEngine,
            )

            self._engine = ModelInferenceEngine()

        return self._engine

    def generate(
        self,
        prompt: str,
        model: Any,
        tokenizer: Any,
        document_base64=None,
    ) -> str:
        """Generate text through the concrete inference engine.

        Args:
            prompt (str): The prompt to send to the model.
            model (Any): The loaded model.
            tokenizer (Any): The tokenizer or processor.
            document_base64: Optional base64 document payload.

        Returns:
            str: The generated text.
        """
        return self._get_engine().generate(
            prompt=prompt,
            model=model,
            tokenizer=tokenizer,
            document_base64=document_base64,
        )
