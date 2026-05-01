from typing import Generator
from ..ports.language_model import LanguageModel
from ..ports.audit_log import AuditLog
from ..ports.session_manager import SessionManager
from domain.entities.llm_request import LLMRequest
from domain.entities.llm_response import LLMResponse
from domain.value_objects.session_id import SessionId
from domain.value_objects.message import Message
from datetime import datetime, UTC
import uuid


class Complete:

    def __init__(
        self,
        session_manager: SessionManager,
        language_model: LanguageModel,
        audit_log: AuditLog
    ):
        self._session_manager = session_manager
        self._language_model = language_model
        self._audit_log = audit_log

    def stream(
        self,
        session_id: SessionId,
        messages: list[Message],
        model: str
    ) -> Generator[str, None, None]:

        session = self._session_manager.validate(session_id)

        request = LLMRequest(
            id=str(uuid.uuid4()),
            session_id=session_id,
            org_id=session.org_id,
            messages=messages,
            model=model,
            created_at=datetime.now(UTC)
        )

        request.mark_sent()
        finish_reason = "unknown"

        try:
            for chunk in self._language_model.stream(messages, model):
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
            self._audit_log.log(request, response)

        except Exception as e:
            request.fail(str(e))
            raise