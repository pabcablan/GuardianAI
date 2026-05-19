import pymupdf

from domain.extracted_document import ExtractedDocument
from domain.parsed_document import ParsedDocument
from infrastructure.ports.text_extractor import TextExtractor


class PyMuPDFTextExtractor(TextExtractor):
    """Extract text from PDFs using PyMuPDF when pages contain real text."""

    async def extract_text(self, document: ParsedDocument) -> ExtractedDocument:
        """Extract text from a parsed PDF document.

        Args:
            document (ParsedDocument): Parsed PDF bytes and metadata.

        Returns:
            ExtractedDocument: Extracted text plus document metadata.
        """
        pdf_content = pymupdf.open(stream=document.content, filetype="pdf")

        extracted_pages: list[str] = []
        for page in pdf_content:
            if self._looks_like_scanned_page(page):
                continue

            text = page.get_text("text").strip()
            if text:
                extracted_pages.append(text)

        extracted_text = "\n\n".join(extracted_pages)

        return ExtractedDocument(
            extracted_text=extracted_text,
            filename=document.filename,
            document_id=document.document_id,
            extraction_method="library",
        )

    def _looks_like_scanned_page(self, page: pymupdf.Page) -> bool:
        """Detect pages that are mostly an image with only sparse overlay text."""
        page_area = page.rect.width * page.rect.height
        if page_area <= 0:
            return False

        image_coverage = self._largest_image_coverage(page, page_area)
        if image_coverage < 0.9:
            return False

        words = page.get_text("words")
        if len(words) > 80:
            return False

        text_area_ratio = self._text_area_ratio(page, page_area)
        return text_area_ratio < 0.08

    def _largest_image_coverage(
        self,
        page: pymupdf.Page,
        page_area: float,
    ) -> float:
        """Return the largest image area relative to the page area."""
        largest_coverage = 0.0

        for image in page.get_images(full=True):
            xref = image[0]
            for rect in page.get_image_rects(xref):
                rect_area = max(0.0, rect.width) * max(0.0, rect.height)
                largest_coverage = max(largest_coverage, rect_area / page_area)

        return largest_coverage

    def _text_area_ratio(
        self,
        page: pymupdf.Page,
        page_area: float,
    ) -> float:
        """Estimate how much of the page is covered by extracted text blocks."""
        text_area = 0.0

        for block in page.get_text("blocks"):
            x0, y0, x1, y1, *_ = block
            text_area += max(0.0, x1 - x0) * max(0.0, y1 - y0)

        return text_area / page_area
