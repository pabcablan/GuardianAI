from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from application.usecases.send_to_llm import SendToLLM
from domain.value_objects.message import Message, Role
from domain.value_objects.anonymized_text import AnonymizedText
from domain.exceptions import ProviderRateLimitError, ProviderConnectionError, ProviderAPIError
from pydantic import BaseModel


class MessageRequest(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: list[MessageRequest]
    model: str

class FastAPIGateway:
    def __init__(self, send_to_llm: SendToLLM):
        self._send_to_llm = send_to_llm
        self._router = APIRouter()
        self._router.add_api_route("/handle", self.handle, methods=["POST"])

    @property
    def router(self):
        return self._router

    async def handle(self, request: ChatRequest) -> StreamingResponse:
        try:
            messages = [
                Message(
                    role=Role(m.role),
                    content=AnonymizedText(m.content)
                )
                for m in request.messages
            ]
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        async def event_stream():
            try:
                async for chunk in self._send_to_llm.stream(messages, request.model):
                    yield f"data: {chunk}\n\n"
                yield "data: [DONE]\n\n"
            except ProviderRateLimitError as error:
                print(f"AI-GATEWAY rate limit error: {error}", flush=True)
                yield f"data: error:429:{error}\n\n"
            except ProviderConnectionError as error:
                print(f"AI-GATEWAY connection error: {error}", flush=True)
                yield f"data: error:503:{error}\n\n"
            except ProviderAPIError as error:
                print(f"AI-GATEWAY provider API error: {error}", flush=True)
                yield f"data: error:502:{error}\n\n"

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
