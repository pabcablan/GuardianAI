from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from application.usecases.create_session import CreateSession
from application.usecases.complete import Complete
from domain.value_objects.session_id import SessionId
from domain.value_objects.message import Message, Role
from domain.value_objects.anonymized_text import AnonymizedText
from domain.exceptions import SessionNotFoundError, ProviderRateLimitError, ProviderConnectionError, ProviderAPIError
from pydantic import BaseModel


class MessageRequest(BaseModel):
    role: str
    content: str


class CompletionRequest(BaseModel):
    session_id: str
    messages: list[MessageRequest]
    model: str


class CreateSessionRequest(BaseModel):
    user_id: str
    org_id: str


class FastAPICompletion:
    def __init__(self, completion: Complete, create_session: CreateSession):
        self._completion = completion
        self._create_session = create_session
        self._router = APIRouter()
        self._router.add_api_route("/session", self.session, methods=["POST"])
        self._router.add_api_route("/complete", self.complete, methods=["POST"])

    def session(self, request: CreateSessionRequest):
        session = self._create_session.execute(
            user_id=request.user_id,
            org_id=request.org_id
        )
        return {"session_id": str(session.session_id)}

    def complete(self, request: CompletionRequest) -> StreamingResponse:
        try:
            session_id = SessionId.from_string(request.session_id)
            messages = [
                Message(
                    role=Role(m.role),
                    content=AnonymizedText(m.content)
                )
                for m in request.messages
            ]
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        def event_stream():
            try:
                for chunk in self._completion.stream(session_id, messages, request.model):
                    yield f"data: {chunk}\n\n"
                yield "data: [DONE]\n\n"
            except SessionNotFoundError:
                yield "data: error:401\n\n"
            except ProviderRateLimitError:
                yield "data: error:429\n\n"
            except ProviderConnectionError:
                yield "data: error:503\n\n"
            except ProviderAPIError:
                yield "data: error:502\n\n"

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
