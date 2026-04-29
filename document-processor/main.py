from fastapi import FastAPI, UploadFile, File

from infrastructure.adapters.fastapi_document_parser import FastAPIDocumentParser
from infrastructure.adapters.markitdown_text_extractor import MarkitdownTextExtractor
from infrastructure.adapters.llm_text_extractor import LLMTextExtractor

from application.usecases.process_document import ProcessDocument

def main():

    parser = FastAPIDocumentParser()
    text_extractor = MarkitdownTextExtractor()
    process_doc = ProcessDocument(parser, text_extractor)

    # TODO make LLMTextExtractor a fallback implementation (own port)

    app = FastAPI(
        title="GuardianAI Document Processor",
        version="0.1.0",
        description="Text extraction API for PDF documents."
    )

    @app.post("/extract")
    async def extract_document(file: UploadFile = File(...)) -> str:
        return await process_doc.execute(file)

if __name__ == "__main__":
    main()
