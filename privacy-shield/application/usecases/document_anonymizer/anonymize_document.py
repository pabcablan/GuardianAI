from infrastructure.ports.anonymization_evaluator import AnonymizationEvaluator
from infrastructure.ports.anonymizer import Anonymizer


class AnonymizeDocument:
    def __init__ (self, evaluator: AnonymizationEvaluator, anonymizer: Anonymizer):
        self.evaluator = evaluator
        self.anonymizer = anonymizer
    
    def execute(self, text: str) -> str:
        if self.evaluator.evaluate(text):
            return self.anonymizer.anonymize(text)
        else:
            return text