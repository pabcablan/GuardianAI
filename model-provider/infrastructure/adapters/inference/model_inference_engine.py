import base64

import pymupdf
import torch
from PIL import Image

from infrastructure.ports.text_generator import TextGenerator


class ModelInferenceEngine(TextGenerator):

    def generate(self, system_prompt: str, prompt: str, model, processor,
                 document_base64: str | None = None) -> str:
        pil_images = (
            self._decode_pdf_document(document_base64)
            if document_base64
            else None
        )
        if pil_images:
            return self._generate_from_document_pages(
                system_prompt=system_prompt,
                prompt=prompt,
                model=model,
                processor=processor,
                pages=pil_images,
            )

        return self._generate_from_text(
            system_prompt=system_prompt,
            prompt=prompt,
            model=model,
            processor=processor,
        )

    def _generate_from_document_pages(
        self,
        system_prompt: str,
        prompt: str,
        model,
        processor,
        pages: list[Image.Image],
    ) -> str:
        page_outputs: list[str] = []

        for page in pages:
            page_outputs.append(
                self._generate_from_single_image(
                    system_prompt=system_prompt,
                    prompt=prompt,
                    model=model,
                    processor=processor,
                    image=page,
                )
            )

        return "\n\n".join(
            output.strip()
            for output in page_outputs
            if output.strip()
        )

    def _generate_from_single_image(
        self,
        system_prompt: str,
        prompt: str,
        model,
        processor,
        image: Image.Image,
    ) -> str:
        messages = self._build_messages(
            system_prompt,
            prompt,
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
        system_prompt: str,
        prompt: str,
        model,
        processor,
    ) -> str:
        messages = self._build_messages(
            system_prompt,
            prompt,
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
        model,
        processor,
        inputs,
    ) -> str:
        pad_token_id = (
            getattr(processor, "pad_token_id", None)
            or processor.tokenizer.pad_token_id
        )

        with torch.inference_mode():
            output_ids = model.generate(
                **inputs,
                max_new_tokens=600,
                temperature=0.01,
                do_sample=True,
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
        system_prompt: str,
        prompt: str,
        image_count: int,
    ) -> list:
        user_content = []
        for _ in range(image_count):
            user_content.append({"type": "image"})
        user_content.append({"type": "text", "text": prompt})

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_content})
        return messages

    def _decode_pdf_document(self, document_base64: str) -> list[Image.Image]:
        """Convierte un PDF base64 a una lista de imágenes (una por página)"""
        pdf_bytes = base64.b64decode(document_base64)
        pdf_document = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        
        images = []
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            # Renderizar página a imagen con alta calidad
            pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2))
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            images.append(img)
        
        pdf_document.close()
        return images
