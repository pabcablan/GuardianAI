from infrastructure.ports.anonymization_evaluator import AnonymizationEvaluator
from infrastructure.ports.anonymizer import Anonymizer


class AnonymizeDocument:
    def __init__ (self, evaluator: AnonymizationEvaluator, anonymizer: Anonymizer):
        self.evaluator = evaluator
        self.anonymizer = anonymizer
    
    async def execute(
        self,
        text: str,
        settings: dict[str, str] | None = None,
    ) -> str:
        if await self.evaluator.evaluate(text):
            return await self.anonymizer.anonymize(text, settings=settings)
        else:
            return text
