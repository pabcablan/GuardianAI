import base64
from io import BytesIO

import fitz
import torch
from PIL import Image
from pypdf import PdfReader

from infrastructure.ports.text_generator import TextGenerator


MAX_DOCUMENT_CONTEXT_CHARS = 12000
DOCUMENT_MAX_NEW_TOKENS = 1024
DEFAULT_MAX_NEW_TOKENS = 160
MAX_VISION_PAGES = 3
PDF_RENDER_ZOOM = 2.0


class ModelInferenceEngine(TextGenerator):
    
    def generate(self, prompt: str, model, tokenizer, document_base64=None) -> str:
        """Generate text using a loaded model and tokenizer.

        Args:
            prompt (str): The prompt to send to the model.
            model: The loaded model.
            tokenizer: The model tokenizer or processor.
            document_base64: Optional base64 document payload to extract text
                from before sending the prompt to the model.

        Returns:
            str: The generated text.
        """
        if document_base64 and self._supports_vision(model, tokenizer):
            return self._generate_with_vision_document(
                prompt=prompt,
                model=model,
                processor=tokenizer,
                document_base64=document_base64,
            )

        content = prompt

        if document_base64:
            content = self._build_prompt_with_document(
                prompt=prompt,
                document_base64=document_base64,
            )

        messages = [{"role": "user", "content": content}]
            
        if hasattr(tokenizer, "apply_chat_template"):
            input_text = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )
        else:
            input_text = f"{content}\n\nRespuesta:"

        device = self._get_model_device(model)
        inputs = tokenizer(text=input_text, return_tensors="pt").to(device)
        max_new_tokens = (
            DOCUMENT_MAX_NEW_TOKENS
            if document_base64
            else DEFAULT_MAX_NEW_TOKENS
        )
        
        with torch.inference_mode():
            output_ids = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                repetition_penalty=1.1,
                pad_token_id=self._get_eos_token_id(tokenizer),
            )

        input_tokens = inputs["input_ids"].shape[1]
        generated_tokens = output_ids[0][input_tokens:]
        return tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()

    def _generate_with_vision_document(
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
        images = self._extract_document_images(document_base64)
        if not images:
            content = self._build_prompt_with_document(
                prompt=prompt,
                document_base64=document_base64,
            )
            return self._generate_text_only(
                content=content,
                model=model,
                tokenizer=processor,
                max_new_tokens=DOCUMENT_MAX_NEW_TOKENS,
            )

        messages = [
            {
                "role": "user",
                "content": [
                    *[
                        {"type": "image", "image": image}
                        for image in images
                    ],
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
        inputs = self._move_inputs_to_device(inputs, self._get_model_device(model))

        with torch.inference_mode():
            output_ids = model.generate(
                **inputs,
                max_new_tokens=DOCUMENT_MAX_NEW_TOKENS,
                do_sample=False,
                repetition_penalty=1.1,
                pad_token_id=self._get_eos_token_id(processor),
            )

        input_tokens = inputs["input_ids"].shape[1]
        generated_tokens = output_ids[:, input_tokens:]
        return processor.batch_decode(
            generated_tokens,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
        )[0].strip()

    def _generate_text_only(
        self,
        content: str,
        model,
        tokenizer,
        max_new_tokens: int,
    ) -> str:
        """Generate text using the text-only path.

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
        inputs = self._move_inputs_to_device(inputs, self._get_model_device(model))

        with torch.inference_mode():
            output_ids = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                repetition_penalty=1.1,
                pad_token_id=self._get_eos_token_id(tokenizer),
            )

        input_tokens = inputs["input_ids"].shape[1]
        generated_tokens = output_ids[0][input_tokens:]
        return tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()

    def _build_prompt_with_document(
        self,
        prompt: str,
        document_base64: str,
    ) -> str:
        """Attach extracted document text to the user prompt.

        Args:
            prompt (str): The original user prompt.
            document_base64 (str): The base64-encoded document bytes.

        Returns:
            str: The prompt enriched with readable document content.
        """
        document_text = self._extract_document_text(document_base64)
        if not document_text:
            return (
                f"{prompt}\n\n"
                "Contenido del documento:\n"
                "[No se pudo extraer texto legible del documento adjunto. "
                "El modelo cargado actualmente es de texto y no puede leer "
                "paginas escaneadas o imagenes sin OCR/VLM.]"
            )

        return (
            f"{prompt}\n\n"
            "Contenido del documento:\n"
            f"{document_text[:MAX_DOCUMENT_CONTEXT_CHARS]}"
        )

    def _extract_document_text(self, document_base64: str) -> str:
        """Extract readable text from a base64 document payload.

        Args:
            document_base64 (str): The base64-encoded document bytes.

        Returns:
            str: The extracted text, or an empty string if no text is readable.
        """
        try:
            document_bytes = base64.b64decode(document_base64, validate=True)
        except ValueError:
            return ""

        if document_bytes.startswith(b"%PDF"):
            return self._extract_pdf_text(document_bytes)

        return self._decode_text_bytes(document_bytes)

    def _extract_document_images(self, document_base64: str) -> list[Image.Image]:
        """Render a base64 document into images for VLM input.

        Args:
            document_base64 (str): The base64-encoded document bytes.

        Returns:
            list[Image.Image]: Rendered document pages or decoded images.
        """
        try:
            document_bytes = base64.b64decode(document_base64, validate=True)
        except ValueError:
            return []

        if document_bytes.startswith(b"%PDF"):
            return self._render_pdf_pages(document_bytes)

        try:
            image = Image.open(BytesIO(document_bytes)).convert("RGB")
        except Exception:
            return []

        return [image]

    def _render_pdf_pages(self, document_bytes: bytes) -> list[Image.Image]:
        """Render the first PDF pages as RGB images.

        Args:
            document_bytes (bytes): The PDF bytes.

        Returns:
            list[Image.Image]: Rendered page images.
        """
        images: list[Image.Image] = []
        try:
            pdf_document = fitz.open(stream=document_bytes, filetype="pdf")
        except Exception:
            return images

        matrix = fitz.Matrix(PDF_RENDER_ZOOM, PDF_RENDER_ZOOM)
        for page_index in range(min(len(pdf_document), MAX_VISION_PAGES)):
            page = pdf_document.load_page(page_index)
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            image = Image.open(BytesIO(pixmap.tobytes("png"))).convert("RGB")
            images.append(image)

        pdf_document.close()
        return images

    def _extract_pdf_text(self, document_bytes: bytes) -> str:
        """Extract text from a PDF text layer.

        Args:
            document_bytes (bytes): The PDF bytes.

        Returns:
            str: The extracted PDF text, or an empty string if unavailable.
        """
        try:
            reader = PdfReader(BytesIO(document_bytes))
            page_texts = [
                page.extract_text() or ""
                for page in reader.pages
            ]
        except Exception:
            return ""

        return "\n\n".join(
            page_text.strip()
            for page_text in page_texts
            if page_text.strip()
        ).strip()

    def _decode_text_bytes(self, document_bytes: bytes) -> str:
        """Decode non-PDF bytes as text when possible.

        Args:
            document_bytes (bytes): The document bytes.

        Returns:
            str: The decoded text, or an empty string if decoding fails.
        """
        for encoding in ("utf-8", "latin-1"):
            try:
                return document_bytes.decode(encoding).strip()
            except UnicodeDecodeError:
                continue

        return ""

    def _get_model_device(self, model):
        """Return the first device used by a model.

        Args:
            model: The loaded model.

        Returns:
            The model device.
        """
        if hasattr(model, "device"):
            return model.device

        return next(model.parameters()).device

    def _supports_vision(self, model, tokenizer) -> bool:
        """Return whether the loaded model can consume images.

        Args:
            model: The loaded model.
            tokenizer: The tokenizer or processor.

        Returns:
            bool: True when vision inputs are supported.
        """
        if hasattr(tokenizer, "image_processor"):
            return True

        config = getattr(model, "config", None)
        return hasattr(config, "vision_config")

    def _move_inputs_to_device(self, inputs, device):
        """Move tensor inputs to a model device.

        Args:
            inputs: The processor/tokenizer output.
            device: The target torch device.

        Returns:
            The moved inputs.
        """
        if hasattr(inputs, "to"):
            return inputs.to(device)

        return {
            key: value.to(device) if hasattr(value, "to") else value
            for key, value in inputs.items()
        }

    def _get_eos_token_id(self, tokenizer) -> int | None:
        """Return an EOS token id from a tokenizer or processor.

        Args:
            tokenizer: The tokenizer or processor.

        Returns:
            int | None: The EOS token id if available.
        """
        if hasattr(tokenizer, "eos_token_id"):
            return tokenizer.eos_token_id

        nested_tokenizer = getattr(tokenizer, "tokenizer", None)
        if nested_tokenizer is not None:
            return getattr(nested_tokenizer, "eos_token_id", None)

        return None
