"""Fake assistant stream gateway used to test streaming deanonymization."""
from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field

from infrastructure.ports.external.assistant_stream_port import (
    AssistantStreamPort,
)


@dataclass
class FakeAssistantStreamGateway(AssistantStreamPort):
    """Return predefined assistant response chunks for tests and demos.

    Attributes:
        responses (dict[str, tuple[str, ...]]): Mapping between prompts and
            fake response chunks.
        default_response (tuple[str, ...]): Fallback chunks returned for
            unknown prompts.
    """

    responses: dict[str, tuple[str, ...]] = field(default_factory=dict)
    default_response: tuple[str, ...] = (
        "The organization [NOM",
        "BRE_1] has document [DOC",
        "_2] and email [CONTACT",
        "O_1].",
    )

    def stream_response(self, prompt: str) -> Iterator[str]:
        """Stream the fake response configured for a prompt.

        Args:
            prompt (str): The anonymized prompt.

        Returns:
            Iterator[str]: The configured fake chunks or the default chunks.
        """
        yield from self.responses.get(prompt, self.default_response)
