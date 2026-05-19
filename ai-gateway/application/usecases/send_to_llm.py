"""Use case for forwarding anonymized messages to the language model."""
from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from uuid import uuid4

from domain.entities.llm_request import LLMRequest
from domain.entities.llm_response import LLMResponse
from domain.value_objects.anonymized_text import AnonymizedText
from domain.value_objects.message import Message, Role
from infrastructure.ports.audit_log import AuditLog
from infrastructure.ports.language_model import LanguageModel


SYSTEM_PROMPT = (
    "You are a helpful assistant. Always respond in the same language as the "
    "user. You may encounter references like [PERSON_1], [DOC_1], or similar "
    "labels. Treat them as you would any named entity and respond naturally."
)


class SendToLLM:
    """Coordinate one audited streaming request to the provider."""

    def __init__(
        self,
        language_model: LanguageModel,
        audit_log: AuditLog,
    ) -> None:
        """Initialize the use case dependencies.

        Args:
            language_model (LanguageModel): The provider adapter used to stream
                response chunks.
            audit_log (AuditLog): The audit adapter used to persist request and
                response metadata.
        """
        self._language_model = language_model
        self._audit_log = audit_log

    async def stream(
        self,
        messages: list[Message],
        model: str,
    ) -> AsyncGenerator[str, None]:
        """Stream provider output for one message sequence.

        Args:
            messages (list[Message]): The anonymized conversation messages.
            model (str): The provider model identifier.

        Yields:
            str: Streamed response chunks from the provider.
        """
        all_messages = [self._build_system_message(), *messages]
        request = self._build_request(
            messages=all_messages,
            model=model,
        )
        request.mark_sent()

        try:
            async for chunk in self._language_model.stream(all_messages, model):
                yield chunk

            request.complete("stop")
            await self._audit_log.log(
                request,
                self._build_response(
                    request_id=request.id,
                    model=model,
                    finish_reason="stop",
                ),
            )
        except Exception as error:
            request.fail(str(error))
            raise

    def _build_system_message(self) -> Message:
        """Build the fixed system instruction prepended to each request.

        Returns:
            Message: The system message sent before user content.
        """
        return Message(
            role=Role.SYSTEM,
            content=AnonymizedText(SYSTEM_PROMPT),
        )

    def _build_request(
        self,
        messages: list[Message],
        model: str,
    ) -> LLMRequest:
        """Build the audited request entity for one streamed interaction.

        Args:
            messages (list[Message]): The conversation messages sent to the
                provider.
            model (str): The provider model identifier.

        Returns:
            LLMRequest: The request entity tracked for audit purposes.
        """
        return LLMRequest(
            id=str(uuid4()),
            org_id="default",
            messages=messages,
            model=model,
            created_at=datetime.now(UTC),
        )

    def _build_response(
        self,
        request_id: str,
        model: str,
        finish_reason: str,
    ) -> LLMResponse:
        """Build the audited response entity after streaming completes.

        Args:
            request_id (str): The request identifier linked to the response.
            model (str): The provider model identifier.
            finish_reason (str): The provider finish reason.

        Returns:
            LLMResponse: The response entity stored in the audit log.
        """
        return LLMResponse(
            id=str(uuid4()),
            request_id=request_id,
            model=model,
            prompt_tokens=0,
            completion_tokens=0,
            finish_reason=finish_reason,
            completed_at=datetime.now(UTC),
        )
