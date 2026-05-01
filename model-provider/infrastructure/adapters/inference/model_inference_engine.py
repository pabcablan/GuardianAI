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
            output_ids = model.generate(**inputs, max_new_tokens=600, temperature=0.01, do_sample=False, repetition_penalty=1.1)

        input_tokens = inputs["input_ids"].shape[1]
        generated_tokens = output_ids[0][input_tokens:]
        return tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()