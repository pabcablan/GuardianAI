import uvicorn
from fastapi import FastAPI

from infrastructure.adapters.evaluation.qwen_evaluator import QwenEvaluator
from infrastructure.adapters.anonymization.llm_anonymizer import LlmAnonymizer
from infrastructure.adapters.model_loader.unsloth_provider import UnslothProvider

from application.usecases.document_anonymizer.anonymize_document import AnonymizeDocument

def main():
    unsloth_provider = UnslothProvider()

    model_anonymizer, tokenizer_anonymizer = unsloth_provider.load(model_id="unsloth/Qwen3.5-0.8B",  name="anonymizer_model")

    evaluator = QwenEvaluator(model=model_anonymizer, tokenizer=tokenizer_anonymizer)
    anonymizer = LlmAnonymizer(model=model_anonymizer, tokenizer=tokenizer_anonymizer)

    anonymize_usecase = AnonymizeDocument(evaluator=evaluator, anonymizer=anonymizer)
    
    app = FastAPI()

    @app.post("/anonymize")
    def anonymize_route(text: str):
        return anonymize_usecase.execute(text)

    uvicorn.run(app, host="0.0.0.0", port=7002)

if __name__ == "__main__":
    main()