import base64

import httpx


class LLMClient:
    def __init__(
        self,
        base_url: str,
        model_name: str,
        timeout_seconds: float = 600.0,
    ) -> None:
        self._base_url = base_url
        self._model_name = model_name
        self._timeout_seconds = timeout_seconds

    async def generate(self, prompt: str, content: bytes) -> str:
        document_base64 = base64.b64encode(content).decode("ascii")
        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            response = await client.post(
                f"{self._base_url}/generate_response/",
                json={
                    "model_name": self._model_name,
                    "prompt": prompt,
                    "document_base64": document_base64,
                }
            )
            response.raise_for_status()
            payload = response.json()
            if isinstance(payload, str):
                return payload

            return str(payload)
