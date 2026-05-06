import json
from datetime import datetime, UTC

import aiofiles
from application.ports.audit_log import AuditLog
from domain.entities.llm_request import LLMRequest
from domain.entities.llm_response import LLMResponse
from domain.value_objects import Role


class FileAuditLog(AuditLog):

    def __init__(self, file_path: str):
        self._file_path = file_path

    async def log(self, request: LLMRequest, response: LLMResponse) -> None:
        entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "request": {
                "id": request.id,
                "org_id": request.org_id,
                "model": request.model,
                "status": request.status.value,
                "created_at": request.created_at.isoformat(),
                "failure_reason": request.failure_reason,
                "messages": [m.to_dict() for m in request.messages if m.role != Role.SYSTEM]
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

        async with aiofiles.open(self._file_path, mode="a") as f:
            await f.write(json.dumps(entry) + "\n")