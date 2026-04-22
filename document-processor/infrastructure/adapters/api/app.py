from __future__ import annotations

from fastapi import FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware

from application.usecases.extract_document import ExtractDocumentCommand
from infrastructure.adapters.api.dependencies import build_container
from infrastructure.adapters.api.schemas import ExtractDocumentResponse


container = build_container()

app = FastAPI(
    title="GuardianAI Document Processor",
    version="0.1.0",
    description="API del modulo document-processor para extraer texto de PDFs.",
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


@app.post(
    "/api/documents/extract",
    response_model=ExtractDocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def extract_document(
    file: UploadFile = File(...),
) -> ExtractDocumentResponse:
    try:
        result = container.extract_document.execute(
            ExtractDocumentCommand(
                filename=file.filename or "document.pdf",
                content_type=file.content_type or "",
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

    return ExtractDocumentResponse(
        document_id=result.document_id,
        filename=result.filename,
        extracted_text=result.extracted_text,
        page_count=result.page_count,
    )
