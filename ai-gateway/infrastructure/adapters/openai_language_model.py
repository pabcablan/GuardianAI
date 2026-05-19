"""OpenAI-backed language model adapter for ai-gateway."""
from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Literal, cast

from openai import APIConnectionError, APIStatusError, AsyncOpenAI, RateLimitError
from openai.types.responses import EasyInputMessageParam

from domain.exceptions import (
    ProviderAPIError,
    ProviderConnectionError,
    ProviderRateLimitError,
)
from domain.value_objects.message import Message
from infrastructure.ports.language_model import LanguageModel


class OpenAILanguageModel(LanguageModel):
    """Stream responses from the OpenAI Responses API."""

    def __init__(self, api_key: str) -> None:
        """Initialize the OpenAI client.

        Args:
            api_key (str): The OpenAI API key used for requests.
        """
        self.client = AsyncOpenAI(api_key=api_key)

    async def stream(
        self,
        messages: list[Message],
        model: str,
    ) -> AsyncGenerator[str, None]:
        """Stream text deltas from the configured OpenAI model.

        Args:
            messages (list[Message]): The normalized conversation messages.
            model (str): The OpenAI model identifier.

        Yields:
            str: Streamed response chunks from OpenAI.
        """
        input_messages = self._build_input_messages(messages)

        try:
            async with self.client.responses.stream(
                model=model,
                input=input_messages,
            ) as stream:
                async for event in stream:
                    if event.type == "response.output_text.delta":
                        yield event.delta
        except RateLimitError as error:
            raise ProviderRateLimitError(str(error))
        except APIConnectionError as error:
            raise ProviderConnectionError(str(error))
        except APIStatusError as error:
            raise ProviderAPIError(str(error))

    def _build_input_messages(
        self,
        messages: list[Message],
    ) -> list[EasyInputMessageParam]:
        """Convert domain messages into OpenAI input messages.

        Args:
            messages (list[Message]): The normalized conversation messages.

        Returns:
            list[EasyInputMessageParam]: The OpenAI-compatible input payload.
        """
        return [
            EasyInputMessageParam(
                role=cast(
                    Literal["user", "assistant", "system", "developer"],
                    message.role.value,
                ),
                content=str(message.content),
            )
            for message in messages
        ]
