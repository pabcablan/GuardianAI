"""HTTP entrypoint for the ai-gateway service."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
import uvicorn

from application.usecases.send_to_llm import SendToLLM
from infrastructure.adapters.fastapi_gateway import FastAPIGateway
from infrastructure.adapters.file_audit_log import FileAuditLog
from infrastructure.adapters.openai_language_model import OpenAILanguageModel


def create_app() -> FastAPI:
    """Create the FastAPI application for ai-gateway.

    Returns:
        FastAPI: The configured application instance.

    Raises:
        RuntimeError: If the OpenAI API key is missing.
    """
    current_dir = Path(__file__).parent
    load_dotenv(current_dir / ".env")
    load_dotenv(current_dir.parent / ".env")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is required to start the ai-gateway service."
        )

    app = FastAPI(
        title="GuardianAI AI Gateway",
        version="0.1.0",
        description="Streams assistant responses through a provider adapter.",
    )

    language_model = OpenAILanguageModel(api_key=api_key)
    audit_log = FileAuditLog(file_path=str(current_dir / "audit.log"))
    send_to_llm = SendToLLM(
        language_model=language_model,
        audit_log=audit_log,
    )
    fastapi_gateway = FastAPIGateway(send_to_llm=send_to_llm)

    app.include_router(fastapi_gateway.router)
    return app


def main() -> None:
    """Run the ai-gateway development server."""
    uvicorn.run(app, host="0.0.0.0", port=8005)


app = create_app()


if __name__ == "__main__":
    main()
