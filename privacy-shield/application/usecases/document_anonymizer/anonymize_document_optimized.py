from infrastructure.ports.anonymization_evaluator import AnonymizationEvaluator
from infrastructure.ports.anonymizer import Anonymizer


class AnonymizeDocumentOptimized:
    def __init__(self, anonymizer: Anonymizer):
        self.anonymizer = anonymizer
    
    async def execute(
        self,
        text: str,
        settings: dict[str, str] | None = None,
    ) -> dict:
        return await self.anonymizer.anonymize(text, settings=settings)
