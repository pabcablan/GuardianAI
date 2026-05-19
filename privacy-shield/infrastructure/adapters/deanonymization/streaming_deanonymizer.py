import re

from infrastructure.ports.deanonymizer import Deanonymizer


class StreamingDeanonymizer(Deanonymizer):
    """Restore placeholders incrementally while preserving chunk boundaries."""

    def __init__(self) -> None:
        self.buffer = ""
        self.partial_pattern = re.compile(r"\[[A-Z_0-9]*$")

    def deanonymize(self, text: str, replacements: dict[str, str]) -> str:
        """Restore placeholders from one streamed fragment.

        Args:
            text (str): Incoming chunk that may contain full or partial tags.
            replacements (dict[str, str]): Placeholder-to-original mapping.

        Returns:
            str: Safe restored text that can be emitted immediately.
        """
        self.buffer += text

        match = self.partial_pattern.search(self.buffer)

        if match:
            split_index = match.start()
            safe_text = self.buffer[:split_index]
            self.buffer = self.buffer[split_index:]
        else:
            safe_text = self.buffer
            self.buffer = ""

        for tag, original in replacements.items():
            safe_text = safe_text.replace(tag, original)

        return safe_text

    def flush(self, replacements: dict[str, str]) -> str:
        """Restore any buffered tail once the stream has completed.

        Args:
            replacements (dict[str, str]): Placeholder-to-original mapping.

        Returns:
            str: Remaining restored text buffered across previous chunks.
        """
        remaining_text = self.buffer
        self.buffer = ""
        for tag, original in replacements.items():
            remaining_text = remaining_text.replace(tag, original)
        return remaining_text
