import json
import aiofiles
from datetime import datetime, UTC
from application.ports.audit_log import AuditLog
from domain.entities.llm_request import LLMRequest
from domain.entities.llm_response import LLMResponse


class FileAuditLog(AuditLog):

    def __init__(self, file_path: str):
        self._file_path = file_path

    def log(self, request: LLMRequest, response: LLMResponse) -> None:
        entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "request": {
                "id": request.id,
                "session_id": str(request.session_id),
                "org_id": request.org_id,
                "model": request.model,
                "status": request.status.value,
                "created_at": request.created_at.isoformat(),
                "failure_reason": request.failure_reason
            },
            "response": {
                "id": response.id,
                "request_id": response.request_id,
                "model": response.model,
                "prompt_tokens": response.prompt_tokens,
                "completion_tokens": response.completion_tokens,
                "finish_reason": response.finish_reason,
                "completed_at": response.completed_at.isoformat()
            }
        }

        with open(self._file_path, mode="a") as f:
            f.write(json.dumps(entry) + "\n")