"""PyMuPDF adapter for building anonymized PDF previews."""
from __future__ import annotations

from io import BytesIO
from typing import Any
import re

import fitz

from infrastructure.ports.anonymized_pdf_builder_port import (
    AnonymizedPdfBuilderPort,
)


class PyMuPdfAnonymizedPdfBuilder(AnonymizedPdfBuilderPort):
    """Overlay visible PDF text occurrences with placeholder labels."""

    _NAMESPACED_PLACEHOLDER_PATTERN = re.compile(
        r"^\[([A-F0-9]{8})_(.+)\]$",
        re.IGNORECASE,
    )

    def build(
        self,
        pdf_content: bytes,
        replacements: dict[str, str],
    ) -> bytes:
        """Build an anonymized PDF from original bytes and replacements.

        Args:
            pdf_content (bytes): The original PDF bytes.
            replacements (dict[str, str]): Placeholder-to-original mappings.

        Returns:
            bytes: The anonymized PDF bytes.

        Raises:
            ValueError: If none of the original values can be located.
        """
        document = fitz.open(stream=pdf_content, filetype="pdf")
        replacement_count = 0

        try:
            for page in document:
                page_replacements: list[tuple[Any, str]] = []
                for placeholder, original_value in replacements.items():
                    original_text = original_value.strip()
                    if not original_text:
                        continue

                    for area in self._find_text_areas(page, original_text):
                        page_replacements.append((area, placeholder))

                if page_replacements:
                    for area, placeholder in page_replacements:
                        display_placeholder = self._display_placeholder(
                            placeholder,
                        )
                        text_area = self._build_text_area(
                            page,
                            area,
                            display_placeholder,
                        )
                        page.draw_rect(
                            text_area,
                            color=(1, 1, 1),
                            fill=(1, 1, 1),
                            width=0,
                            overlay=True,
                        )
                        page.insert_textbox(
                            text_area,
                            display_placeholder,
                            fontsize=self._resolve_font_size(area),
                            color=(0, 0, 0),
                            align=fitz.TEXT_ALIGN_LEFT,
                        )
                    replacement_count += len(page_replacements)

            if replacement_count == 0:
                raise ValueError(
                    "No se pudo generar una vista visual anonimizada para "
                    "este PDF. Puede que sea escaneado o que el texto no sea "
                    "seleccionable."
                )

            output = BytesIO()
            document.save(output, garbage=4, deflate=True)
            return output.getvalue()
        finally:
            document.close()

    def _find_text_areas(
        self,
        page: fitz.Page,
        original_text: str,
    ) -> list[fitz.Rect]:
        """Locate precise replacement areas for one original text value.

        Args:
            page (fitz.Page): The page that contains the text.
            original_text (str): The original visible text to locate.

        Returns:
            list[fitz.Rect]: Matching text rectangles on the page.
        """
        line_matches = self._find_line_word_matches(page, original_text)
        if line_matches:
            return line_matches

        return self._deduplicate_rects(page.search_for(original_text))

    def _find_line_word_matches(
        self,
        page: fitz.Page,
        original_text: str,
    ) -> list[fitz.Rect]:
        """Match one text value against contiguous words on the same line."""
        target_tokens = self._tokenize_search_text(original_text)
        if not target_tokens:
            return []

        words = sorted(
            page.get_text("words"),
            key=lambda word: (
                int(word[5]),
                int(word[6]),
                int(word[7]),
            ),
        )
        matches: list[fitz.Rect] = []
        token_count = len(target_tokens)

        for index in range(len(words) - token_count + 1):
            window = words[index : index + token_count]
            first_word = window[0]

            if any(
                int(word[5]) != int(first_word[5]) or
                int(word[6]) != int(first_word[6])
                for word in window[1:]
            ):
                continue

            window_tokens = [
                self._normalize_search_token(str(word[4]))
                for word in window
            ]
            if window_tokens != target_tokens:
                continue

            rect = fitz.Rect(
                min(float(word[0]) for word in window),
                min(float(word[1]) for word in window),
                max(float(word[2]) for word in window),
                max(float(word[3]) for word in window),
            )
            matches.append(rect)

        return self._deduplicate_rects(matches)

    def _build_text_area(
        self,
        page: fitz.Page,
        area: fitz.Rect,
        placeholder: str,
    ) -> fitz.Rect:
        """Build a white overlay area sized for one placeholder label."""
        fontsize = self._resolve_font_size(area)
        placeholder_width = fitz.get_text_length(
            placeholder,
            fontname="helv",
            fontsize=fontsize,
        )
        horizontal_padding = 6
        vertical_padding = 1.5
        target_width = max(
            area.width + horizontal_padding,
            placeholder_width + horizontal_padding,
        )

        return fitz.Rect(
            area.x0,
            max(page.rect.y0, area.y0 - vertical_padding),
            min(page.rect.x1, area.x0 + target_width),
            min(page.rect.y1, area.y1 + vertical_padding),
        )

    def _resolve_font_size(self, area: fitz.Rect) -> float:
        """Return a conservative font size that stays inside one text row."""
        return max(6, min(10, area.height * 0.72))

    def _tokenize_search_text(self, value: str) -> list[str]:
        """Split one search value into normalized tokens."""
        return [
            self._normalize_search_token(token)
            for token in value.split()
            if self._normalize_search_token(token)
        ]

    def _normalize_search_token(self, token: str) -> str:
        """Normalize one token for exact visual matching on the page."""
        return " ".join(token.strip().split()).casefold()

    def _deduplicate_rects(self, rects: list[fitz.Rect]) -> list[fitz.Rect]:
        """Drop duplicate rectangles produced by repeated matching paths."""
        unique_rects: list[fitz.Rect] = []
        seen: set[tuple[int, int, int, int]] = set()

        for rect in rects:
            key = (
                round(rect.x0 * 10),
                round(rect.y0 * 10),
                round(rect.x1 * 10),
                round(rect.y1 * 10),
            )
            if key in seen:
                continue
            seen.add(key)
            unique_rects.append(rect)

        return unique_rects

    def _display_placeholder(self, placeholder: str) -> str:
        """Return a user-facing placeholder without the session namespace."""
        match = self._NAMESPACED_PLACEHOLDER_PATTERN.fullmatch(placeholder)
        if not match:
            return placeholder
        return f"[{match.group(2)}]"
