"""Run a console demo of streaming privacy-shield deanonymization.

Edit `STREAM_CHUNKS` and run this file from the `privacy-shield` directory with:

`..\\.venv\\Scripts\\python.exe run_deanonymization_demo.py`
"""
from __future__ import annotations

import json
from pathlib import Path

from application.usecases.stream_safe_response import (
    StreamSafeResponseCommand,
    StreamSafeResponseUseCase,
)
from infrastructure.adapters.fake_assistant_stream_gateway import (
    FakeAssistantStreamGateway,
)


ANONYMIZED_PROMPT = "Summarize this anonymized requirement."

STREAM_CHUNKS = (
    "Me ha encantado tu respuesta. Es muy importante [NOM",
    "BRE_1] que tu email [CONT",
    "ACTO_1] sea el que corresponde con tu documento [DOC",
    "_2].",
)

REPLACEMENTS_FILE = Path(__file__).with_name("REQUERIMIENTO.json")


def load_replacements(path: Path) -> dict[str, str]:
    """Load the placeholder replacement map from a JSON file.

    Args:
        path (Path): The JSON file that contains the replacement map.

    Returns:
        dict[str, str]: The placeholder-to-original-value mapping.
    """
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    """Run the streaming deanonymization demo."""
    replacements = load_replacements(REPLACEMENTS_FILE)
    gateway = FakeAssistantStreamGateway(
        responses={ANONYMIZED_PROMPT: STREAM_CHUNKS}
    )
    use_case = StreamSafeResponseUseCase(gateway)

    print("Streaming chunks received from the assistant:")
    for index, chunk in enumerate(STREAM_CHUNKS, start=1):
        print(f"Chunk {index}: {chunk!r}")

    print()
    print("Deanonymized chunks emitted to the user:")
    emitted_chunks: list[str] = []
    for index, chunk in enumerate(
        use_case.execute(
            StreamSafeResponseCommand(
                anonymized_prompt=ANONYMIZED_PROMPT,
                replacements=replacements,
                strict=True,
            )
        ),
        start=1,
    ):
        emitted_chunks.append(chunk)
        print(f"Emitted {index}: {chunk!r}")

    print()
    print("Final deanonymized response:")
    print("".join(emitted_chunks))


if __name__ == "__main__":
    main()
