from __future__ import annotations

import re
from io import BytesIO

from pypdf import PdfReader

from domain.document import ExtractionProgress, ExtractionProgressCallback
from infrastructure.adapters.extract_vlm import extract_pdf_text


MIN_DIRECT_TEXT_LENGTH = 20
MIN_ALNUM_RATIO = 0.5
MAX_SUSPICIOUS_RATIO = 0.15


def extract_pdf_text_with_fallback(
    pdf_bytes: bytes,
    *,
    progress_callback: ExtractionProgressCallback | None = None,
) -> tuple[str, int]:
    _notify_direct_extraction_started(progress_callback=progress_callback)
    extracted_text, page_count = try_extract_pdf_text(pdf_bytes)
    if extracted_text is not None:
        _notify_direct_extraction_completed(º
            page_count,
            progress_callback=progress_callback,
        )
        return extracted_text, page_count

    _notify_vlm_fallback(
        page_count,
        progress_callback=progress_callback,
    )
    return extract_pdf_text(
        pdf_bytes,
        progress_callback=progress_callback,
    )


def try_extract_pdf_text(pdf_bytes: bytes) -> tuple[str | None, int]:
    reader = PdfReader(BytesIO(pdf_bytes))
    page_texts = [
        _normalize_page_text(page.extract_text() or "")
        for page in reader.pages
    ]
    page_count = len(page_texts)

    if not page_texts:
        return "", 0

    if not all(_is_text_layer_usable(text) for text in page_texts):
        return None, page_count

    extracted_text = "\n\n".join(text for text in page_texts if text).strip()
    if not extracted_text:
        return None, page_count

    return extracted_text, page_count


def _normalize_page_text(text: str) -> str:
    normalized_text = text.replace("\x00", " ")
    normalized_text = re.sub(r"[ \t]+\n", "\n", normalized_text)
    normalized_text = re.sub(r"\n{3,}", "\n\n", normalized_text)
    return normalized_text.strip()


def _is_text_layer_usable(text: str) -> bool:
    compact_text = re.sub(r"\s+", " ", text).strip()
    if len(compact_text) < MIN_DIRECT_TEXT_LENGTH:
        return False

    visible_characters = [character for character in compact_text if not character.isspace()]
    if not visible_characters:
        return False

    alnum_ratio = sum(character.isalnum() for character in visible_characters) / len(
        visible_characters
    )
    suspicious_ratio = sum(
        _is_suspicious_character(character) for character in visible_characters
    ) / len(visible_characters)

    return (
        alnum_ratio >= MIN_ALNUM_RATIO
        and suspicious_ratio <= MAX_SUSPICIOUS_RATIO
    )


def _is_suspicious_character(character: str) -> bool:
    return (
        character == "\uFFFD"
        or character in {"\u25A1", "\u25A0"}
        or 0xE000 <= ord(character) <= 0xF8FF
    )


def _notify_direct_extraction_completed(
    page_count: int,
    *,
    progress_callback: ExtractionProgressCallback | None,
) -> None:
    if progress_callback is None:
        return

    total_pages = max(page_count, 1)
    progress_callback(
        ExtractionProgress(
            stage="completed",
            current=page_count,
            total=total_pages,
            message=(
                "Extraccion directa completada usando la capa de texto del PDF."
            ),
        )
    )


def _notify_direct_extraction_started(
    *,
    progress_callback: ExtractionProgressCallback | None,
) -> None:
    if progress_callback is None:
        return

    progress_callback(
        ExtractionProgress(
            stage="starting",
            current=0,
            total=1,
            message="Extrayendo texto usando la capa interna del PDF.",
        )
    )


def _notify_vlm_fallback(
    page_count: int,
    *,
    progress_callback: ExtractionProgressCallback | None,
) -> None:
    if progress_callback is None:
        return

    total_pages = max(page_count, 1)
    progress_callback(
        ExtractionProgress(
            stage="starting",
            current=0,
            total=total_pages,
            message=(
                "La capa de texto del PDF no es fiable. Se usara extraccion con VLM."
            ),
        )
    )
