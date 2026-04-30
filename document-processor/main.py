import uvicorn
from fastapi import FastAPI, UploadFile, File

from infrastructure.adapters.fastapi_document_parser import FastAPIDocumentParser
from infrastructure.adapters.markitdown_text_extractor import MarkitdownTextExtractor
from infrastructure.adapters.llm_text_extractor import LLMTextExtractor
from infrastructure.utils.text_extraction_fallback import FallbackTextExtractor
from infrastructure.utils.llm_client import LLMClient

from application.usecases.process_document import ProcessDocument


def build_app() -> FastAPI:
    """Build the document processor FastAPI application.

    Returns:
        FastAPI: The configured document processor API.
    """
    llm_client = LLMClient(base_url="http://localhost:8000")  # Change to real LLM API URL

    parser = FastAPIDocumentParser()
    text_extractor = FallbackTextExtractor(
        primary=MarkitdownTextExtractor(),
        fallback=LLMTextExtractor(llm_client),
        min_chars=25
    )
    process_doc = ProcessDocument(parser, text_extractor)

    app = FastAPI(
        title="GuardianAI Document Processor",
        version="0.1.0",
        description="Text extraction API for PDF documents."
    )

    @app.post("/extract")
    async def extract_document(file: UploadFile = File(...)) -> str:
        return await process_doc.execute(file)

    return app


app = build_app()


def main():
    """Run the document processor API."""
    uvicorn.run(app, host="0.0.0.0", port=8001)


if __name__ == "__main__":
    main()
