from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from infrastructure.adapters.openai_language_model import OpenAILanguageModel
from infrastructure.adapters.file_audit_log import FileAuditLog
from infrastructure.adapters.memory_session_manager import MemorySessionManager
from infrastructure.adapters.fastapi_completion import FastAPICompletion
from application.usecases.complete import Complete
from application.usecases.create_session import CreateSession
import os

load_dotenv(Path(__file__).parent.parent / ".env")
app = FastAPI()

language_model = OpenAILanguageModel(api_key=os.getenv("OPENAI_API_KEY"))
audit_log = FileAuditLog(file_path="audit.log")
session_manager = MemorySessionManager(session_ttl_minutes=60)

complete = Complete(
    session_manager=session_manager,
    language_model=language_model,
    audit_log=audit_log
)
create_session = CreateSession(session_manager=session_manager)

fastapi_completion = FastAPICompletion(
    completion=complete,
    create_session=create_session
)

app.include_router(fastapi_completion._router)