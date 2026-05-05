"""Main inference adapter for model-provider."""
from __future__ import annotations

from infrastructure.adapters.inference.document_payload import (
    DocumentPayloadReader,
)
from infrastructure.adapters.inference.model_runtime import supports_vision
from infrastructure.adapters.inference.text_inference_engine import (
    TextInferenceEngine,
)
from infrastructure.adapters.inference.vision_inference_engine import (
    DOCUMENT_MAX_NEW_TOKENS,
    VisionInferenceEngine,
)
from infrastructure.ports.text_generator import TextGenerator


DEFAULT_MAX_NEW_TOKENS = 160


class ModelInferenceEngine(TextGenerator):
    """Coordinate text and vision inference paths."""

    def __init__(
        self,
        document_reader: DocumentPayloadReader | None = None,
        text_engine: TextInferenceEngine | None = None,
        vision_engine: VisionInferenceEngine | None = None,
    ) -> None:
        """Initialize the inference coordinator.

        Args:
            document_reader (DocumentPayloadReader | None): Document reader.
            text_engine (TextInferenceEngine | None): Text inference engine.
            vision_engine (VisionInferenceEngine | None): Vision engine.
        """
        self._document_reader = document_reader or DocumentPayloadReader()
        self._text_engine = text_engine or TextInferenceEngine()
        self._vision_engine = vision_engine or VisionInferenceEngine(
            document_reader=self._document_reader,
            text_engine=self._text_engine,
        )

    def generate(
        self,
        prompt: str,
        model,
        tokenizer,
        document_base64=None,
    ) -> str:
        """Generate text using a loaded model and tokenizer.

        Args:
            prompt (str): The prompt to send to the model.
            model: The loaded model.
            tokenizer: The model tokenizer or processor.
            document_base64: Optional base64 document payload.

        Returns:
            str: The generated text.
        """
        if document_base64 and supports_vision(model, tokenizer):
            return self._vision_engine.generate(
                prompt=prompt,
                model=model,
                processor=tokenizer,
                document_base64=document_base64,
            )

        content = prompt
        max_new_tokens = DEFAULT_MAX_NEW_TOKENS
        if document_base64:
            content = self._document_reader.build_prompt_with_document(
                prompt=prompt,
                document_base64=document_base64,
            )
            max_new_tokens = DOCUMENT_MAX_NEW_TOKENS

        return self._text_engine.generate(
            content=content,
            model=model,
            tokenizer=tokenizer,
            max_new_tokens=max_new_tokens,
        )


"""
import torch
from infrastructure.ports.text_generator import TextGenerator
from infrastructure.ports.model_repository import ModelRepository

class ModelInferenceEngine(TextGenerator):

def generate(self, prompt: str, model, tokenizer, document_base64=None) -> str:

messages = [{"role": "user", "content": prompt}]

if document_base64:
messages[0]["content"] += "\n\n[DOCUMENTO ADJUNTO]"

input_text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
inputs = tokenizer(text=input_text, return_tensors="pt").to(model.device)

        with torch.no_grad():
        with torch.inference_mode():
output_ids = model.generate(**inputs, max_new_tokens=600, temperature=0.01, do_sample=False, repetition_penalty=1.1)

input_tokens = inputs["input_ids"].shape[1]
generated_tokens = output_ids[0][input_tokens:]
"""