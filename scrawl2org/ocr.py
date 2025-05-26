"""OCR (Optical Character Recognition) functionality for page images."""

from typing import Any, Dict


def extract_text_from_image(
    image_data: bytes, page_number: int = None, pdf_filename: str = None
) -> Dict[str, Any]:
    """Extract text from page image using OCR.

    Args:
        image_data: PNG image data as bytes
        page_number: Page number (optional, for logging/debugging)
        pdf_filename: PDF filename (optional, for logging/debugging)

    Returns:
        Dictionary containing OCR results with at least a 'text' field
    """
    # TODO: Replace with actual OCR implementation
    # Consider using libraries like:
    # - pytesseract (Tesseract OCR)
    # - easyocr
    # - paddleocr
    # - Azure Cognitive Services
    # - Google Cloud Vision API

    debug_info = "DEBUG STUB INFO"
    if page_number is not None:
        debug_info += f" - Page {page_number}"
    if pdf_filename:
        debug_info += f" from {pdf_filename}"

    return {
        "text": debug_info,
        "confidence": 1.0,
        "processing_time_ms": 0,
        "engine": "stub",
        "version": "0.1.0",
    }

