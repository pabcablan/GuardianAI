from __future__ import annotations

import asyncio
import json

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from application.usecases.extract_document import ExtractDocumentCommand
from domain.document import ExtractionProgress
from infrastructure.adapters.api.dependencies import build_container
from infrastructure.adapters.api.schemas import (
    ExtractionCompletedResponse,
    ExtractionErrorResponse,
    ExtractionProgressResponse,
)


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


@app.post("/api/documents/extract-stream")
async def extract_document_stream(
    file: UploadFile = File(...),
) -> StreamingResponse:
    filename = file.filename or "document.pdf"
    content_type = file.content_type or ""
    content = await file.read()

    async def event_stream():
        queue: asyncio.Queue[dict[str, object] | None] = asyncio.Queue()
        loop = asyncio.get_running_loop()

        def emit_progress(progress: ExtractionProgress) -> None:
            payload = ExtractionProgressResponse(
                stage=progress.stage,
                current=progress.current,
                total=progress.total,
                message=progress.message,
            ).model_dump()
            loop.call_soon_threadsafe(queue.put_nowait, payload)

        def run_extraction() -> None:
            try:
                result = container.extract_document.execute(
                    ExtractDocumentCommand(
                        filename=filename,
                        content_type=content_type,
                        content=content,
                    ),
                    progress_callback=emit_progress,
                )
            except (RuntimeError, ValueError) as error:
                payload = ExtractionErrorResponse(detail=str(error)).model_dump()
                loop.call_soon_threadsafe(queue.put_nowait, payload)
            except Exception as error:
                payload = ExtractionErrorResponse(
                    detail=f"Unexpected extraction error: {error}",
                ).model_dump()
                loop.call_soon_threadsafe(queue.put_nowait, payload)
            else:
                payload = ExtractionCompletedResponse(
                    document_id=result.document_id,
                    filename=result.filename,
                    extracted_text=result.extracted_text,
                    page_count=result.page_count,
                ).model_dump()
                loop.call_soon_threadsafe(queue.put_nowait, payload)
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, None)

        task = asyncio.create_task(asyncio.to_thread(run_extraction))

        while True:
            item = await queue.get()
            if item is None:
                break
            yield json.dumps(item, ensure_ascii=True) + "\n"

        await task

    return StreamingResponse(
        event_stream(),
        media_type="application/x-ndjson",
    )
