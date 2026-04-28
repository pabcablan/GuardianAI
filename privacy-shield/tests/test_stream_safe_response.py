"""Tests for the privacy-shield streaming deanonymization flow."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from application.usecases.stream_safe_response import (
    StreamSafeResponseCommand,
    StreamSafeResponseUseCase,
)
from domain.streaming_deanonymization import StreamingDeanonymizer
from infrastructure.adapters.fake_assistant_stream_gateway import (
    FakeAssistantStreamGateway,
)


class StreamingDeanonymizerTest(unittest.TestCase):
    """Verify placeholder restoration while text arrives in chunks."""

    def test_restores_split_placeholders(self) -> None:
        """Restore placeholders even when they are split across chunks."""
        deanonymizer = StreamingDeanonymizer(
            {
                "[NOMBRE_1]": "FEDERACION INSULAR",
                "[DOC_2]": "V38902953",
            }
        )
        chunks = (
            "The entity [NOM",
            "BRE_1] has document [DOC",
            "_2].",
        )

        streamed_text = "".join(deanonymizer.push(chunk) for chunk in chunks)
        streamed_text += deanonymizer.flush()

        self.assertEqual(
            streamed_text,
            "The entity FEDERACION INSULAR has document V38902953.",
        )

    def test_holds_partial_placeholder(self) -> None:
        """Avoid emitting incomplete placeholder fragments to the user."""
        deanonymizer = StreamingDeanonymizer({"[NOMBRE_1]": "Known Name"})

        first_output = deanonymizer.push("Hello [NOM")
        second_output = deanonymizer.push("BRE_1].")

        self.assertEqual(first_output, "Hello ")
        self.assertEqual(second_output, "Known Name.")

    def test_rejects_complete_unknown_placeholder(self) -> None:
        """Reject unknown complete placeholders while streaming in strict mode."""
        deanonymizer = StreamingDeanonymizer({"[NOMBRE_1]": "Known Name"})

        with self.assertRaises(ValueError):
            deanonymizer.push("Hello [NOMBRE_99].")


class StreamSafeResponseUseCaseTest(unittest.TestCase):
    """Verify the assistant-stream-to-user-stream use case."""

    def test_streams_restored_fake_assistant_chunks(self) -> None:
        """Restore fake assistant chunks using the provided sample map."""
        sample_path = Path(__file__).resolve().parents[1] / "REQUERIMIENTO.json"
        replacements = json.loads(sample_path.read_text(encoding="utf-8"))
        gateway = FakeAssistantStreamGateway()
        use_case = StreamSafeResponseUseCase(gateway)

        chunks = list(
            use_case.execute(
                StreamSafeResponseCommand(
                    anonymized_prompt="Summarize this anonymized requirement.",
                    replacements=replacements,
                )
            )
        )
        text = "".join(chunks)

        self.assertIn(
            "FEDERACION INSULAR DE TENIS DE MESA LA PALMA",
            text,
        )
        self.assertIn("V38902953", text)
        self.assertIn("gestion_fptm@yahoo.es", text)
        self.assertNotIn("[NOMBRE_1]", text)


if __name__ == "__main__":
    unittest.main()
