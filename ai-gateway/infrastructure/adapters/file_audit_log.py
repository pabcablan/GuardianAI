"""File-based audit log adapter for ai-gateway activity."""
from __future__ import annotations

import json
from datetime import UTC, datetime

import aiofiles

from domain.entities.llm_request import LLMRequest
from domain.entities.llm_response import LLMResponse
from domain.value_objects.message import Role
from infrastructure.ports.audit_log import AuditLog


class FileAuditLog(AuditLog):
    """Persist request and response audit entries to a JSONL file."""

    def __init__(self, file_path: str) -> None:
        """Initialize the target audit log file.

        Args:
            file_path (str): The JSONL file path used to store audit entries.
        """
        self._file_path = file_path

    async def log(self, request: LLMRequest, response: LLMResponse) -> None:
        """Append one request/response audit record to disk.

        Args:
            request (LLMRequest): The audited request metadata.
            response (LLMResponse): The audited response metadata.
        """
        entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "request": {
                "id": request.id,
                "org_id": request.org_id,
                "model": request.model,
                "status": request.status.value,
                "created_at": request.created_at.isoformat(),
                "failure_reason": request.failure_reason,
                "messages": [
                    message.to_dict()
                    for message in request.messages
                    if message.role != Role.SYSTEM
                ],
            },
            "response": {
                "id": response.id,
                "request_id": response.request_id,
                "model": response.model,
                "prompt_tokens": response.prompt_tokens,
                "completion_tokens": response.completion_tokens,
                "finish_reason": response.finish_reason,
                "completed_at": response.completed_at.isoformat(),
            },
        }

        async with aiofiles.open(self._file_path, mode="a") as file_handle:
            await file_handle.write(json.dumps(entry) + "\n")
