"""PDF processing and image extraction."""

import sys
from pathlib import Path

import fitz  # PyMuPDF

from .database import Database
from .ocr import extract_text_from_image


class PDFProcessor:
    """Processes PDF files and extracts page images."""

    def __init__(self, db_path: str = "scrawl2org.db"):
        self.db = Database(db_path)

    def process_pdf(self, pdf_path: str, force_update: bool = False) -> None:
        """Process a PDF file and store page images in database.

        Args:
            pdf_path: Path to the PDF file
            force_update: If True, process all pages even if unchanged
        """
        pdf_path = str(Path(pdf_path).resolve())

        if not Path(pdf_path).exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        # Check if PDF has changed
        has_changed, pdf_file_id = self.db.check_pdf_changed(pdf_path)

        if not has_changed and not force_update:
            print(f"PDF unchanged, skipping: {pdf_path}")
            return

        print(f"Processing PDF: {pdf_path}")

        # Update PDF file record
        pdf_file_id = self.db.update_pdf_file(pdf_path, pdf_file_id)

        # Open PDF and extract pages
        doc = fitz.open(pdf_path)
        try:
            page_count = len(doc)
            print(f"Found {page_count} pages")

            for page_num in range(page_count):
                self._process_page(doc, page_num, pdf_file_id, force_update)

            # Clean up pages that no longer exist
            self.db.delete_old_pages(pdf_file_id, page_count)

        finally:
            doc.close()

        print(f"Completed processing: {pdf_path}")

    def _process_page(
        self, doc: fitz.Document, page_num: int, pdf_file_id: int, force_update: bool
    ):
        """Process a single page and store its image."""
        page = doc[page_num]

        # Render page to image (PNG format)
        pix = page.get_pixmap(
            matrix=fitz.Matrix(2.0, 2.0)
        )  # 2x scaling for better quality
        image_data = pix.tobytes("png")

        # Check if we need to update this page
        if not force_update:
            existing_hash = self.db.get_existing_page_image(pdf_file_id, page_num)
            current_hash = self.db.get_image_hash(image_data)

            if existing_hash == current_hash:
                print(f"  Page {page_num + 1}: unchanged, skipping")
                return

        # Print status update to stderr
        print(f"  Page {page_num + 1}: processing...", file=sys.stderr)

        # Perform OCR on the image
        pdf_filename = Path(doc.name).name if hasattr(doc, "name") else "unknown.pdf"
        ocr_result = extract_text_from_image(image_data, page_num + 1, pdf_filename)

        # Store the image with OCR text
        self.db.store_page_image(pdf_file_id, page_num, image_data, ocr_result)

        # Print completion status with OCR text to stderr
        ocr_text = ocr_result.get("text", "").strip()
        print(
            f"  Page {page_num + 1}: completed OCR ({len(image_data)} bytes)",
            file=sys.stderr,
        )
        if ocr_text:
            # Print the full OCR text without truncation
            print(f"  OCR text: {ocr_text}", file=sys.stderr)
        else:
            print("  OCR text: (no text detected)", file=sys.stderr)

    def get_page_count(self, pdf_path: str) -> int:
        """Get the number of pages in a PDF file."""
        doc = fitz.open(pdf_path)
        try:
            return len(doc)
        finally:
            doc.close()

    def extract_page_image(self, pdf_path: str, page_num: int) -> bytes:
        """Extract a single page as PNG image data."""
        doc = fitz.open(pdf_path)
        try:
            if page_num >= len(doc):
                raise ValueError(f"Page {page_num} does not exist in PDF")

            page = doc[page_num]
            pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
            return pix.tobytes("png")
        finally:
            doc.close()
