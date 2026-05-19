from infrastructure.ports.deanonymizer import Deanonymizer


class DeanonymizeDocumentStream:
    """Restore placeholders from streamed assistant output."""

    def __init__(self, deanonymizer: Deanonymizer) -> None:
        self.deanonymizer = deanonymizer

    async def execute(
        self,
        chunks: list[str],
        replacements: dict[str, str],
    ):
        """Restore placeholders from a streamed response in order.

        Args:
            chunks (list[str]): Assistant stream fragments to restore.
            replacements (dict[str, str]): Placeholder-to-original mapping.

        Yields:
            str: Deanonymized text fragments ready to stream back to clients.
        """
        for chunk in chunks:
            restored = self.deanonymizer.deanonymize(chunk, replacements)
            if restored:
                yield restored

        if hasattr(self.deanonymizer, "flush"):
            restored_final = self.deanonymizer.flush(replacements)
            if restored_final:
                yield restored_final
