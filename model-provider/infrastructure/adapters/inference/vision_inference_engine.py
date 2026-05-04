"""Vision-language model inference."""
from __future__ import annotations

import torch

from infrastructure.adapters.inference.document_payload import (
    DocumentPayloadReader,
)
from infrastructure.adapters.inference.model_runtime import (
    get_eos_token_id,
    get_model_device,
    move_inputs_to_device,
)
from infrastructure.adapters.inference.text_inference_engine import (
    TextInferenceEngine,
)


DOCUMENT_MAX_NEW_TOKENS = 1024


class VisionInferenceEngine:
    """Generate responses using rendered document pages as image inputs."""

    def __init__(
        self,
        document_reader: DocumentPayloadReader | None = None,
        text_engine: TextInferenceEngine | None = None,
    ) -> None:
        """Initialize the vision inference engine.

        Args:
            document_reader (DocumentPayloadReader | None): Document reader.
            text_engine (TextInferenceEngine | None): Text fallback engine.
        """
        self._document_reader = document_reader or DocumentPayloadReader()
        self._text_engine = text_engine or TextInferenceEngine()

    def generate(
        self,
        prompt: str,
        model,
        processor,
        document_base64: str,
    ) -> str:
        """Generate text from a prompt and rendered document pages.

        Args:
            prompt (str): The user prompt.
            model: The loaded vision-language model.
            processor: The model processor.
            document_base64 (str): The base64-encoded document.

        Returns:
            str: The generated text.
        """
        images = self._document_reader.extract_document_images(document_base64)
        if not images:
            content = self._document_reader.build_prompt_with_document(
                prompt=prompt,
                document_base64=document_base64,
            )
            return self._text_engine.generate(
                content=content,
                model=model,
                tokenizer=processor,
                max_new_tokens=DOCUMENT_MAX_NEW_TOKENS,
            )

        messages = [
            {
                "role": "user",
                "content": [
                    *[{"type": "image", "image": image} for image in images],
                    {"type": "text", "text": prompt},
                ],
            }
        ]
        input_text = processor.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
        inputs = processor(
            text=[input_text],
            images=images,
            return_tensors="pt",
        )
        inputs = move_inputs_to_device(inputs, get_model_device(model))

        with torch.inference_mode():
            output_ids = model.generate(
                **inputs,
                max_new_tokens=DOCUMENT_MAX_NEW_TOKENS,
                do_sample=False,
                repetition_penalty=1.1,
                pad_token_id=get_eos_token_id(processor),
            )

        input_tokens = inputs["input_ids"].shape[1]
        generated_tokens = output_ids[:, input_tokens:]
        return processor.batch_decode(
            generated_tokens,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
        )[0].strip()
