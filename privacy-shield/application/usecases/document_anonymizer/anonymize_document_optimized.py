from infrastructure.ports.anonymizer import Anonymizer


class AnonymizeDocumentOptimized:
    """Coordinate the optimized anonymization flow."""

    def __init__(self, anonymizer: Anonymizer) -> None:
        self.anonymizer = anonymizer

    async def execute(
        self,
        text: str,
        settings: dict[str, str] | None = None,
    ) -> dict:
        """Run the optimized anonymization use case.

        Args:
            text (str): Source text that may contain sensitive information.
            settings (dict[str, str] | None): UI-selected anonymization modes.

        Returns:
            dict: Anonymized text and placeholder replacement mapping.
        """
        return await self.anonymizer.anonymize(text, settings=settings)
