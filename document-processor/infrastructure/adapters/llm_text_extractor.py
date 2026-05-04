from infrastructure.utils.llm_client import LLMClient
from domain.parsed_document import ParsedDocument
from domain.extracted_document import ExtractedDocument
from infrastructure.ports.text_extractor import TextExtractor

class LLMTextExtractor(TextExtractor):
    def __init__(self, llm_client: LLMClient):
        self._llm_client = llm_client

    async def extract_text(self, document: ParsedDocument) -> ExtractedDocument:
        prompt = '''
        Transcribe todo el texto de este documento exactamente como aparece.
        Manten el contenido literal. No añadas explicaciones. No inventes texto.
        No resumas nada. Manten la estructura del texto. Si hay tablas, mantenlas como tablas. 
        Si hay listas, mantenlas como listas. Si algo no se lee bien, mantenlo lo mas fiel 
        posible a lo visible.
                '''

        extracted_text = await self._llm_client.generate(prompt, document.content)

        return ExtractedDocument(document_id=document.document_id, 
                                 filename=document.filename,
                                 extracted_text=extracted_text)
    

