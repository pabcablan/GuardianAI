from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware

from application.usecases.extract_document import ExtractDocumentUseCase

controller = ExtractDocumentUseCase()

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

app.post("/api/documents/extract", response_model=None, status_code=status.HTTP_201_CREATED)
(controller.execute)
