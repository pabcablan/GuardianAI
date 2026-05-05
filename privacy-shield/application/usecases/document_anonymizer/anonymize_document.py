from infrastructure.ports.anonymization_evaluator import AnonymizationEvaluator
from infrastructure.ports.anonymizer import Anonymizer


class AnonymizeDocument:
    def __init__ (self, evaluator: AnonymizationEvaluator, anonymizer: Anonymizer):
        self.evaluator = evaluator
        self.anonymizer = anonymizer
    
    async def execute(self, text: str) -> str:
        if await self.evaluator.evaluate(text):
            return await self.anonymizer.anonymize(text)
        else:
            return text