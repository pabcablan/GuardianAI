from infrastructure.ports.deanonymizer import Deanonymizer

class DeanonymizeDocumentStream:
    def __init__(self, deanonymizer: Deanonymizer):
        self.deanonymizer = deanonymizer

    async def execute(self, chunks: list[str], replacements: dict[str, str]):
        for chunk in chunks:
            restored = self.deanonymizer.deanonymize(chunk, replacements)
            if restored:
                yield restored
        
        if hasattr(self.deanonymizer, "flush"):
            restored_final = self.deanonymizer.flush(replacements)
            if restored_final:
                yield restored_final