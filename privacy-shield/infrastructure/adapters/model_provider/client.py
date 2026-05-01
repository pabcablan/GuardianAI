"""HTTP client for consuming the model-provider service."""
from __future__ import annotations

from dataclasses import dataclass
import json
import time
from typing import Any

import httpx


class ModelProviderClientError(RuntimeError):
    """Represent a failure when communicating with model-provider."""


@dataclass(frozen=True)
class ModelProviderClient:
    """Call model-provider HTTP endpoints.

    Attributes:
        base_url (str): The model-provider API base URL.
        timeout_seconds (float): The request timeout in seconds.
    """

    base_url: str = "http://127.0.0.1:8006"
    timeout_seconds: float = 600.0
    retry_attempts: int = 20
    retry_delay_seconds: float = 3.0

    def generate_response(
        self,
        model_name: str,
        prompt: str,
        document_base64: str | None = None,
    ) -> str:
        """Generate text using a model-provider model.

        Args:
            model_name (str): The loaded model name.
            prompt (str): The prompt sent to the model.
            document_base64 (str | None): Optional document encoded as base64.

        Returns:
            str: The generated text.
        """
        payload = {
            "model_name": model_name,
            "prompt": prompt,
            "document_base64": document_base64,
        }
        return self._post_json_text("/generate_response/", payload)

    def _post_json_text(self, path: str, payload: dict[str, Any]) -> str:
        """Send JSON to model-provider and return its textual response.

        Args:
            path (str): The model-provider endpoint path.
            payload (dict[str, Any]): The request body.

        Returns:
            str: The parsed textual response.
        """
        last_error: httpx.RequestError | None = None
        for attempt in range(1, self.retry_attempts + 1):
            try:
                with httpx.Client(timeout=self.timeout_seconds) as client:
                    response = client.post(
                        f"{self.base_url}{path}",
                        json=payload,
                    )
                    self._raise_for_status(response)
                    text_response = self._parse_text_response(response)
                    self._raise_for_error_message(text_response)
                    return text_response
            except httpx.RequestError as error:
                last_error = error
                if attempt == self.retry_attempts:
                    break
                time.sleep(self.retry_delay_seconds)

        raise ModelProviderClientError(
            "Model-provider service is unavailable."
        ) from last_error

    def _parse_text_response(self, response: httpx.Response) -> str:
        """Parse a FastAPI string response.

        Args:
            response (httpx.Response): The model-provider response.

        Returns:
            str: The text response.
        """
        try:
            payload = response.json()
        except ValueError:
            return response.text

        if isinstance(payload, str):
            return payload

        return str(payload)

    def _raise_for_error_message(self, text_response: str) -> None:
        """Raise an error when model-provider returns an error string.

        Args:
            text_response (str): The model-provider text response.

        Raises:
            ModelProviderClientError: If model-provider returned an error
            message with HTTP 200.
        """
        if text_response.startswith("Error "):
            raise ModelProviderClientError(text_response)

    def _raise_for_status(self, response: httpx.Response) -> None:
        """Raise a domain error when model-provider returns an HTTP error.

        Args:
            response (httpx.Response): The response to validate.

        Raises:
            ModelProviderClientError: If the response has an error status.
        """
        if response.is_success:
            return

        detail = response.text or "No error detail returned."
        try:
            payload = response.json()
        except json.JSONDecodeError:
            pass
        else:
            if isinstance(payload, dict):
                detail = str(payload.get("detail", detail))

        raise ModelProviderClientError(
            "Model-provider request failed with status "
            f"{response.status_code}: "
            f"{detail}"
        )
