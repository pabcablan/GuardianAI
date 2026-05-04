"""Utilities to read document payloads sent to the model-provider."""
from __future__ import annotations

import base64
from io import BytesIO

import fitz
from PIL import Image
from pypdf import PdfReader


MAX_DOCUMENT_CONTEXT_CHARS = 12000
MAX_VISION_PAGES = 3
PDF_RENDER_ZOOM = 2.0


class DocumentPayloadReader:
    """Extract text and images from base64 document payloads."""

    def build_prompt_with_document(
        self,
        prompt: str,
        document_base64: str,
    ) -> str:
        """Attach extracted document text to the user prompt.

        Args:
            prompt (str): The original user prompt.
            document_base64 (str): The base64-encoded document bytes.

        Returns:
            str: The prompt enriched with readable document content.
        """
        document_text = self.extract_document_text(document_base64)
        if not document_text:
            return (
                f"{prompt}\n\n"
                "Contenido del documento:\n"
                "[No se pudo extraer texto legible del documento adjunto. "
                "El modelo cargado actualmente es de texto y no puede leer "
                "paginas escaneadas o imagenes sin OCR/VLM.]"
            )

        return (
            f"{prompt}\n\n"
            "Contenido del documento:\n"
            f"{document_text[:MAX_DOCUMENT_CONTEXT_CHARS]}"
        )

    def extract_document_text(self, document_base64: str) -> str:
        """Extract readable text from a base64 document payload.

        Args:
            document_base64 (str): The base64-encoded document bytes.

        Returns:
            str: The extracted text, or an empty string if no text is readable.
        """
        document_bytes = self._decode_base64(document_base64)
        if document_bytes is None:
            return ""

        if document_bytes.startswith(b"%PDF"):
            return self._extract_pdf_text(document_bytes)

        return self._decode_text_bytes(document_bytes)

    def extract_document_images(
        self,
        document_base64: str,
    ) -> list[Image.Image]:
        """Render a base64 document into images for VLM input.

        Args:
            document_base64 (str): The base64-encoded document bytes.

        Returns:
            list[Image.Image]: Rendered document pages or decoded images.
        """
        document_bytes = self._decode_base64(document_base64)
        if document_bytes is None:
            return []

        if document_bytes.startswith(b"%PDF"):
            return self._render_pdf_pages(document_bytes)

        try:
            image = Image.open(BytesIO(document_bytes)).convert("RGB")
        except Exception:
            return []

        return [image]

    def _decode_base64(self, document_base64: str) -> bytes | None:
        """Decode a base64 document payload.

        Args:
            document_base64 (str): The base64 document payload.

        Returns:
            bytes | None: The decoded bytes, or None if invalid.
        """
        try:
            return base64.b64decode(document_base64, validate=True)
        except ValueError:
            return None

    def _render_pdf_pages(self, document_bytes: bytes) -> list[Image.Image]:
        """Render the first PDF pages as RGB images.

        Args:
            document_bytes (bytes): The PDF bytes.

        Returns:
            list[Image.Image]: Rendered page images.
        """
        images: list[Image.Image] = []
        try:
            pdf_document = fitz.open(stream=document_bytes, filetype="pdf")
        except Exception:
            return images

        matrix = fitz.Matrix(PDF_RENDER_ZOOM, PDF_RENDER_ZOOM)
        for page_index in range(min(len(pdf_document), MAX_VISION_PAGES)):
            page = pdf_document.load_page(page_index)
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            image = Image.open(BytesIO(pixmap.tobytes("png"))).convert("RGB")
            images.append(image)

        pdf_document.close()
        return images

    def _extract_pdf_text(self, document_bytes: bytes) -> str:
        """Extract text from a PDF text layer.

        Args:
            document_bytes (bytes): The PDF bytes.

        Returns:
            str: The extracted PDF text, or an empty string if unavailable.
        """
        try:
            reader = PdfReader(BytesIO(document_bytes))
            page_texts = [page.extract_text() or "" for page in reader.pages]
        except Exception:
            return ""

        return "\n\n".join(
            page_text.strip()
            for page_text in page_texts
            if page_text.strip()
        ).strip()

    def _decode_text_bytes(self, document_bytes: bytes) -> str:
        """Decode non-PDF bytes as text when possible.

        Args:
            document_bytes (bytes): The document bytes.

        Returns:
            str: The decoded text, or an empty string if decoding fails.
        """
        for encoding in ("utf-8", "latin-1"):
            try:
                return document_bytes.decode(encoding).strip()
            except UnicodeDecodeError:
                continue

        return ""
