import base64
import torch
from PIL import Image
from io import BytesIO
from infrastructure.ports.text_generator import TextGenerator


class ModelInferenceEngine(TextGenerator):

    def generate(self, system_prompt: str, prompt: str, model, processor,
                 images_base64: str | None = None) -> str:

        pil_images = self._decode_images(images_base64) if images_base64 else None

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

    def _decode_images(self, images_base64: list[str]) -> list[Image.Image]:
        return [Image.open(BytesIO(base64.b64decode(img))) for img in images_base64]