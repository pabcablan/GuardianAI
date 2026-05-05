import base64

import httpx

#TODO maybe make this an adapter
class LLMClient:
    def __init__(self, base_url) -> None:
        self._base_url = base_url                       #TODO put it in config or .env

    async def generate(self, prompt: str, content: bytes) -> str:
        async with httpx.AsyncClient(timeout=6000.0) as client:
            content_64 = self.bytes_to_64(content)

            response = await client.post(
                f"{self._base_url}/generate_response/",
                json={
                "model_name": "jd",
                "prompt": prompt,
                "document_base64": content_64
                }
            )
            response.raise_for_status()

            return response.text
        
    def bytes_to_64(self, content: bytes) -> str:
        return base64.b64encode(content).decode()
