from domain.extracted_document import ExtractedDocument
from domain.parsed_document import ParsedDocument
from infrastructure.ports.text_extractor import TextExtractor
from infrastructure.utils.llm_client import LLMClient


DOCUMENT_TRANSCRIPTION_PROMPT = """
Transcribe todo el texto de este documento exactamente como aparece.
Manten el contenido literal. No anadas explicaciones. No inventes texto.
No resumas nada. Manten la estructura del texto.
Si hay tablas, mantenlas como tablas.
Si hay listas, mantenlas como listas.
Si algo no se lee bien, mantenlo lo mas fiel posible a lo visible.
""".strip()


class LLMTextExtractor(TextExtractor):
    """Extract text from a document by delegating to model-provider."""

    def __init__(self, llm_client: LLMClient) -> None:
        self._llm_client = llm_client

    async def extract_text(self, document: ParsedDocument) -> ExtractedDocument:
        """Extract text with the fallback vision-language model.

        Args:
            document (ParsedDocument): Parsed document bytes and metadata.

        Returns:
            ExtractedDocument: Extracted text plus document metadata.
        """
        extracted_text = await self._llm_client.generate(
            DOCUMENT_TRANSCRIPTION_PROMPT,
            document.content,
        )

        return ExtractedDocument(
            document_id=document.document_id,
            filename=document.filename,
            extracted_text=extracted_text,
            extraction_method="model",
        )
