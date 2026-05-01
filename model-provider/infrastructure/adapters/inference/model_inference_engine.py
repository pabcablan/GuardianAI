import torch
from infrastructure.ports.text_generator import TextGenerator

class ModelInferenceEngine(TextGenerator):
    
    def generate(self, prompt: str, model, tokenizer, document_base64=None) -> str:
        """Generate text using a loaded model and tokenizer.

        Args:
            prompt (str): The prompt to send to the model.
            model: The loaded model.
            tokenizer: The model tokenizer or processor.
            document_base64: Optional document payload. It is not decoded here.

        Returns:
            str: The generated text.
        """
        messages = [{"role": "user", "content": prompt}]

        if document_base64:
            messages[0]["content"] += "\n\n[DOCUMENTO ADJUNTO]"
            
        if hasattr(tokenizer, "apply_chat_template"):
            input_text = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )
        else:
            input_text = f"{prompt}\n\nRespuesta JSON:"

        device = self._get_model_device(model)
        inputs = tokenizer(text=input_text, return_tensors="pt").to(device)
        
        with torch.inference_mode():
            output_ids = model.generate(
                **inputs,
                max_new_tokens=160,
                do_sample=False,
                repetition_penalty=1.1,
                pad_token_id=tokenizer.eos_token_id,
            )

        input_tokens = inputs["input_ids"].shape[1]
        generated_tokens = output_ids[0][input_tokens:]
        return tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()

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
