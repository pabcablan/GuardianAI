from typing import AsyncGenerator

from domain.value_objects import AnonymizedText
from ..ports.language_model import LanguageModel
from ..ports.audit_log import AuditLog
from domain.entities.llm_request import LLMRequest
from domain.entities.llm_response import LLMResponse
from domain.value_objects.message import Message, Role
from datetime import datetime, UTC
import uuid


SYSTEM_PROMPT = "You are a helpful assistant"

class SendToLLM:

    def __init__(
        self,
        language_model: LanguageModel,
        audit_log: AuditLog
    ):
        self._language_model = language_model
        self._audit_log = audit_log

    async def stream(
        self,
        messages: list[Message],
        model: str
    ) -> AsyncGenerator[str, None]:

        system_message = Message(
            role=Role.SYSTEM,
            content=AnonymizedText(SYSTEM_PROMPT)
        )

        all_messages = [system_message] + messages

        request = LLMRequest(
            id=str(uuid.uuid4()),
            org_id="default",
            messages=all_messages,
            model=model,
            created_at=datetime.now(UTC)
        )

        request.mark_sent()
        finish_reason = "unknown"

        try:
            async for chunk in self._language_model.stream(all_messages, model):
                yield chunk

            finish_reason = "stop"
            request.complete(finish_reason)

            response = LLMResponse(
                id=str(uuid.uuid4()),
                request_id=request.id,
                model=model,
                prompt_tokens=0,
                completion_tokens=0,
                finish_reason=finish_reason,
                completed_at=datetime.now(UTC)
            )
            await self._audit_log.log(request, response)

        except Exception as e:
            request.fail(str(e))
            raise