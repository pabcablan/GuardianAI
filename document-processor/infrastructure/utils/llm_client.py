import base64
import os

import httpx


class LLMClient:
    """Small HTTP client for the shared model-provider service."""

    def __init__(self, base_url: str | None) -> None:
        """Initialize the model-provider client.

        Args:
            base_url (str | None): Base URL of the model-provider service.
        """
        self._base_url = base_url
        self._model_name = os.getenv("DOCUMENT_MODEL_NAME", "qwen3.5")

    async def generate(self, prompt: str, content: bytes) -> str:
        """Send a document transcription request to model-provider.

        Args:
            prompt (str): Extraction prompt sent to the model.
            content (bytes): Raw document bytes encoded as base64 for transport.

        Returns:
            str: Raw text response returned by model-provider.
        """
        async with httpx.AsyncClient(timeout=6000.0) as client:
            content_64 = self.bytes_to_base64(content)

            response = await client.post(
                f"{self._base_url}/generate_response",
                json={
                    "model_name": self._model_name,
                    "prompt": prompt,
                    "document_base64": content_64,
                },
            )
            response.raise_for_status()

            return response.text

    def bytes_to_base64(self, content: bytes) -> str:
        """Encode raw document bytes as base64 text.

        Args:
            content (bytes): Raw document content.

        Returns:
            str: Base64-encoded payload ready for JSON transport.
        """
        return base64.b64encode(content).decode()
