"""Text-only model inference."""
from __future__ import annotations

import torch

from infrastructure.adapters.inference.model_runtime import (
    get_eos_token_id,
    get_model_device,
    move_inputs_to_device,
)


class TextInferenceEngine:
    """Generate responses with text-only model inputs."""

    def generate(
        self,
        content: str,
        model,
        tokenizer,
        max_new_tokens: int,
    ) -> str:
        """Generate text using a loaded model and tokenizer.

        Args:
            content (str): The text prompt.
            model: The loaded model.
            tokenizer: The tokenizer or processor.
            max_new_tokens (int): The generation token budget.

        Returns:
            str: The generated text.
        """
        messages = [{"role": "user", "content": content}]
        if hasattr(tokenizer, "apply_chat_template"):
            input_text = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )
        else:
            input_text = f"{content}\n\nRespuesta:"

        inputs = tokenizer(text=input_text, return_tensors="pt")
        inputs = move_inputs_to_device(inputs, get_model_device(model))

        with torch.inference_mode():
            output_ids = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                repetition_penalty=1.1,
                pad_token_id=get_eos_token_id(tokenizer),
            )

        input_tokens = inputs["input_ids"].shape[1]
        generated_tokens = output_ids[0][input_tokens:]
        return tokenizer.decode(
            generated_tokens,
            skip_special_tokens=True,
        ).strip()
