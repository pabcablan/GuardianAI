import base64
import torch
import pymupdf
from PIL import Image
from io import BytesIO
from infrastructure.ports.text_generator import TextGenerator


class ModelInferenceEngine(TextGenerator):

    def generate(self, system_prompt: str, prompt: str, model, processor,
                 document_base64: str | None = None) -> str:

        pil_images = self._decode_pdf_document(document_base64) if document_base64 else None

        messages = self._build_messages(system_prompt, prompt, has_images=bool(pil_images))
        input_text = processor.apply_chat_template(messages, add_generation_prompt=True)

        if pil_images:
            inputs = processor(
                pil_images[0] if len(pil_images) == 1 else pil_images,
                input_text,
                add_special_tokens=False,
                return_tensors="pt",
            ).to(model.device)
        else:
            inputs = processor(
                text=input_text,
                images=None,
                return_tensors="pt",
            ).to(model.device)

        pad_token_id = getattr(processor, "pad_token_id", None) or processor.tokenizer.pad_token_id

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

        return processor.decode(generated_tokens, skip_special_tokens=True).strip()

    def _build_messages(self, system_prompt: str, prompt: str, has_images: bool) -> list:
        user_content = []
        if has_images:
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
            pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2))  # 2x zoom para mejor calidad
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            images.append(img)
        
        pdf_document.close()
        return images