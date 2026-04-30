import httpx


class LLMClient:
    def __init__(self, base_url) -> None:
        self._base_url = base_url                       #TODO put it in config or .env

    async def generate(self, prompt: str, content: bytes) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._base_url}/generate",
                files={
                    "document": content,
                },
                data={
                    "prompt": prompt,
                }
            )
            response.raise_for_status()
            return response.text