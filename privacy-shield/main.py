from infrastructure.adapters.model_loader.unsloth_provider import UnslothProvider
from infrastructure.adapters.evaluation.qwen_evaluator import QwenEvaluator
from infrastructure.adapters.anonymization.llm_anonymizer import LlmAnonymizer

def main():
    text_to_process = "Hola, soy Juan Pérez y mi DNI es 12345678Z."
    
    provider = UnslothProvider()
    model, tokenizer = provider.load(model_id="unsloth/Qwen3.5-0.8B", name="privacy_model", gpu_index=0)
    
    evaluator = QwenEvaluator(model, tokenizer)
    anonymizer = LlmAnonymizer(model, tokenizer)
    
    print(f"Texto original: {text_to_process}")
    
    needs_anon = evaluator.evaluate(text_to_process)
    
    if needs_anon:
        print("El texto contiene PII. Anonimizando...")
        anonymized_text, mapping = anonymizer.anonymize_text(text_to_process)
        print(f"Texto anonimizado: {anonymized_text}")
        print(f"Mapping: {mapping}")
    else:
        print("El texto es seguro, no necesita anonimización.")

if __name__ == "__main__":
    main()