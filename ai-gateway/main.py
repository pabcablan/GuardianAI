from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from infrastructure.adapters.openai_language_model import OpenAILanguageModel
from infrastructure.adapters.file_audit_log import FileAuditLog
from infrastructure.adapters.fastapi_gateway import FastAPIGateway
from application.usecases.send_to_llm import SendToLLM
import os

load_dotenv(Path(__file__).parent.parent / ".env")
app = FastAPI()

language_model = OpenAILanguageModel(api_key=os.getenv("OPENAI_API_KEY"))
audit_log = FileAuditLog(file_path="audit.log")

send_to_llm = SendToLLM(
    language_model=language_model,
    audit_log=audit_log
)

fastapi_gateway= FastAPIGateway(send_to_llm=send_to_llm)

app.include_router(fastapi_gateway._router)