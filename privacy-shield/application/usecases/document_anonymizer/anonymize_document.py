from infrastructure.ports.anonymization_evaluator import AnonymizationEvaluator
from infrastructure.ports.anonymizer import Anonymizer


class AnonymizeDocument:
    def __init__ (self, evaluator: AnonymizationEvaluator, anonymizer: Anonymizer):
        self.evaluator = evaluator
        self.anonymizer = anonymizer
    
    def execute(self, text: str) -> str:
        should_anonymize = self.evaluator.evaluate(text)
        print(
            "PRIVACY-SHIELD evaluator "
            f"should_anonymize={should_anonymize} "
            f"text_len={len(text)}",
            flush=True,
        )
        if should_anonymize:
            return self.anonymizer.anonymize(text)
        else:
            return text
