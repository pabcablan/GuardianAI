"""Inference adapter for text and PDF-based model generation."""
from __future__ import annotations

import base64
from typing import Any

import pymupdf
import torch
from PIL import Image

from infrastructure.ports.text_generator import TextGenerator


class ModelInferenceEngine(TextGenerator):
    """Generate model responses from text prompts or PDF document pages."""

    def generate(
        self,
        system_prompt: str | None,
        prompt: str,
        model: Any,
        processor: Any,
        document_base64: str | None = None,
    ) -> str:
        """Generate one response from text-only or PDF-backed input.

        Args:
            system_prompt (str | None): Optional system instructions.
            prompt (str): The user prompt or extraction instruction.
            model (Any): The loaded model object.
            processor (Any): The paired processor or tokenizer.
            document_base64 (str | None): Optional base64-encoded PDF content.

        Returns:
            str: The generated response text.
        """
        pages = (
            self._decode_pdf_document(document_base64)
            if document_base64
            else None
        )

        if pages:
            return self._generate_from_document_pages(
                system_prompt=system_prompt,
                prompt=prompt,
                model=model,
                processor=processor,
                pages=pages,
            )

        return self._generate_from_text(
            system_prompt=system_prompt,
            prompt=prompt,
            model=model,
            processor=processor,
        )

    def _generate_from_document_pages(
        self,
        system_prompt: str | None,
        prompt: str,
        model: Any,
        processor: Any,
        pages: list[Image.Image],
    ) -> str:
        """Generate and concatenate one response per PDF page.

        Args:
            system_prompt (str | None): Optional system instructions.
            prompt (str): The extraction or generation prompt.
            model (Any): The loaded model object.
            processor (Any): The paired processor or tokenizer.
            pages (list[Image.Image]): Rendered PDF pages.

        Returns:
            str: The combined page outputs.
        """
        page_outputs = [
            self._generate_from_single_image(
                system_prompt=system_prompt,
                prompt=prompt,
                model=model,
                processor=processor,
                image=page,
            )
            for page in pages
        ]

        return "\n\n".join(
            output.strip()
            for output in page_outputs
            if output.strip()
        )

    def _generate_from_single_image(
        self,
        system_prompt: str | None,
        prompt: str,
        model: Any,
        processor: Any,
        image: Image.Image,
    ) -> str:
        """Generate one response from a single rendered PDF page.

        Args:
            system_prompt (str | None): Optional system instructions.
            prompt (str): The extraction or generation prompt.
            model (Any): The loaded model object.
            processor (Any): The paired processor or tokenizer.
            image (Image.Image): One rendered PDF page.

        Returns:
            str: The generated page response.
        """
        messages = self._build_messages(
            system_prompt=system_prompt,
            prompt=prompt,
            image_count=1,
        )
        input_text = processor.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
        inputs = processor(
            text=[input_text],
            images=[image],
            add_special_tokens=False,
            padding=True,
            return_tensors="pt",
        ).to(model.device)
        return self._decode_generation(
            model=model,
            processor=processor,
            inputs=inputs,
        )

    def _generate_from_text(
        self,
        system_prompt: str | None,
        prompt: str,
        model: Any,
        processor: Any,
    ) -> str:
        """Generate one response from text-only input.

        Args:
            system_prompt (str | None): Optional system instructions.
            prompt (str): The user prompt.
            model (Any): The loaded model object.
            processor (Any): The paired processor or tokenizer.

        Returns:
            str: The generated response text.
        """
        messages = self._build_messages(
            system_prompt=system_prompt,
            prompt=prompt,
            image_count=0,
        )
        input_text = processor.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
        inputs = processor(
            text=[input_text],
            images=None,
            padding=True,
            return_tensors="pt",
        ).to(model.device)
        return self._decode_generation(
            model=model,
            processor=processor,
            inputs=inputs,
        )

    def _decode_generation(
        self,
        model: Any,
        processor: Any,
        inputs: Any,
    ) -> str:
        """Run generation and decode only the newly produced tokens.

        Args:
            model (Any): The loaded model object.
            processor (Any): The paired processor or tokenizer.
            inputs (Any): The prepared model inputs.

        Returns:
            str: The decoded generated text.
        """
        pad_token_id = (
            getattr(processor, "pad_token_id", None)
            or processor.tokenizer.pad_token_id
        )

        with torch.inference_mode():
            output_ids = model.generate(
                **inputs,
                max_new_tokens=1200,
                temperature=0.01,
                do_sample=False,
                repetition_penalty=1.1,
                pad_token_id=pad_token_id,
            )

        input_tokens = inputs["input_ids"].shape[1]
        generated_tokens = output_ids[0][input_tokens:]
        return processor.decode(
            generated_tokens,
            skip_special_tokens=True,
        ).strip()

    def _build_messages(
        self,
        system_prompt: str | None,
        prompt: str,
        image_count: int,
    ) -> list[dict[str, object]]:
        """Build the chat-template message structure expected by the processor.

        Args:
            system_prompt (str | None): Optional system instructions.
            prompt (str): The user prompt.
            image_count (int): The number of image placeholders to prepend.

        Returns:
            list[dict[str, object]]: The processor message payload.
        """
        user_content: list[dict[str, str]] = []
        for _ in range(image_count):
            user_content.append({"type": "image"})
        user_content.append({"type": "text", "text": prompt})

        messages: list[dict[str, object]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_content})
        return messages

    def _decode_pdf_document(self, document_base64: str) -> list[Image.Image]:
        """Convert a base64-encoded PDF into one image per page.

        Args:
            document_base64 (str): The base64-encoded PDF payload.

        Returns:
            list[Image.Image]: Rendered PDF pages as PIL images.
        """
        pdf_bytes = base64.b64decode(document_base64)
        pdf_document = pymupdf.open(stream=pdf_bytes, filetype="pdf")

        images: list[Image.Image] = []
        for page_index in range(len(pdf_document)):
            page = pdf_document[page_index]
            pixmap = page.get_pixmap(matrix=pymupdf.Matrix(2, 2))
            image = Image.frombytes(
                "RGB",
                (pixmap.width, pixmap.height),
                pixmap.samples,
            )
            images.append(image)

        pdf_document.close()
        return images
