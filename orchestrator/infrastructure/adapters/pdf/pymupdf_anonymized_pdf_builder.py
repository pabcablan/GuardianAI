"""PyMuPDF adapter for building anonymized PDF previews."""
from __future__ import annotations

from io import BytesIO
from typing import Any

import fitz

from infrastructure.ports.anonymized_pdf_builder_port import (
    AnonymizedPdfBuilderPort,
)


class PyMuPdfAnonymizedPdfBuilder(AnonymizedPdfBuilderPort):
    """Replace visible PDF text occurrences using PyMuPDF redactions."""

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

                    for area in page.search_for(original_text):
                        page.add_redact_annot(
                            area,
                            text="",
                            fill=(1, 1, 1),
                        )
                        page_replacements.append((area, placeholder))

                if page_replacements:
                    page.apply_redactions()
                    for area, placeholder in page_replacements:
                        page.insert_textbox(
                            area,
                            placeholder,
                            fontsize=max(6, min(10, area.height * 0.65)),
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
