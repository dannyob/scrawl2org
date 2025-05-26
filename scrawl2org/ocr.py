"""OCR (Optical Character Recognition) functionality for page images."""

import os
from typing import Any, Dict

from .llm_ocr import extract_text_from_image_llm


def extract_text_from_image(
    image_data: bytes, page_number: int = None, pdf_filename: str = None
) -> Dict[str, Any]:
    """Extract text from page image using OCR.

    This function automatically chooses the best available OCR method:
    1. LLM-based OCR (if configured) - uses vision-capable language models
    2. Stub implementation (fallback) - for testing/development

    Args:
        image_data: PNG image data as bytes
        page_number: Page number (optional, for logging/debugging)
        pdf_filename: PDF filename (optional, for logging/debugging)

    Returns:
        Dictionary containing OCR results with at least a 'text' field
    """
    # Check if LLM OCR should be used (environment variable or configuration)
    # Default to True (use LLM OCR) unless explicitly disabled
    use_llm_ocr = os.getenv("SCRAWL2ORG_USE_LLM_OCR", "true").lower() in (
        "true",
        "1",
        "yes",
    )
    llm_model = os.getenv("SCRAWL2ORG_LLM_MODEL", "gemini-1.5-flash-latest")

    if use_llm_ocr:
        try:
            return extract_text_from_image_llm(
                image_data,
                page_number=page_number,
                pdf_filename=pdf_filename,
                model_name=llm_model,
            )
        except Exception as e:
            # Fall back to stub if LLM fails
            print(f"LLM OCR failed, falling back to stub: {e}")

    # Fallback: stub implementation for testing/development
    # TODO: Add other OCR implementations here (tesseract, easyocr, etc.)
    return _extract_text_stub(image_data, page_number, pdf_filename)


def _extract_text_stub(
    image_data: bytes, page_number: int = None, pdf_filename: str = None
) -> Dict[str, Any]:
    """Stub OCR implementation for testing and development.

    Args:
        image_data: PNG image data as bytes
        page_number: Page number (optional, for logging/debugging)
        pdf_filename: PDF filename (optional, for logging/debugging)

    Returns:
        Dictionary containing stub OCR results
    """
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
