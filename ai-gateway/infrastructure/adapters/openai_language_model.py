from openai import OpenAI
from openai.types.responses import EasyInputMessageParam
from openai import RateLimitError, APIConnectionError, APIStatusError
from typing import Generator, List, Literal, cast
from domain.value_objects import Message
from domain.exceptions import ProviderAPIError, ProviderConnectionError, ProviderRateLimitError


class OpenAILanguageModel:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    def stream(self, messages: List[Message], model: str) -> Generator[str, None, None]:
        input_messages: List[EasyInputMessageParam] = [
            EasyInputMessageParam(
                role=cast(Literal["user", "assistant", "system", "developer"], message.role.value),
                content=str(message.content)
            )
            for message in messages
        ]

        try:
            with self.client.responses.stream(
                model=model,
                input=input_messages
            ) as stream:
                for event in stream:
                    if event.type == "response.output_text.delta":
                        yield event.delta
        except RateLimitError as e:
            raise ProviderRateLimitError(str(e))
        except APIConnectionError as e:
            raise ProviderConnectionError(str(e))
        except APIStatusError as e:
            raise ProviderAPIError(str(e))
