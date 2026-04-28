from fastapi import FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware

from application.usecases.extract_document import ExtractedDocumentCommand
from infrastructure.adapters.api.dependencies import build_container #TODO this should be here
from domain.extracted_document import ExtractedDocument


container = build_container()

app = FastAPI(
    title="GuardianAI Document Processor",
    version="0.1.0",
    description="Text extraction API for PDF documents."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}

@app.post("/api/documents/extract", response_model=ExtractedDocument,
          status_code=status.HTTP_201_CREATED)
async def extract_document(file: UploadFile = File(...)) -> ExtractedDocument:
    try:
        result = container.extract_document.execute(
            ExtractedDocumentCommand(
                filename=file.filename,
                content_type=file.content_type,
                content=await file.read(),
            )
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error

    return ExtractedDocument(
        document_id=result.document_id,
        filename=result.filename,
        extracted_text=result.extracted_text,
        num_pages=result.page_count,
    )
