from infrastructure.ports.anonymization_evaluator import AnonymizationEvaluator
from infrastructure.ports.anonymizer import Anonymizer


class AnonymizeDocumentOptimized:
    def __init__(self, anonymizer: Anonymizer):
        self.anonymizer = anonymizer
    
    async def execute(self, text: str) -> dict:
        return await self.anonymizer.anonymize(text)
