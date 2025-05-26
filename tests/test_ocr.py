"""Tests for OCR module."""

from scrawl2org.ocr import extract_text_from_image


def test_extract_text_basic():
    """Test basic OCR text extraction (stub)."""
    image_data = b"fake png image data"
    result = extract_text_from_image(image_data)

    # Should return a dictionary with required fields
    assert isinstance(result, dict)
    assert "text" in result
    assert "confidence" in result
    assert "engine" in result

    # Text should contain debug info
    assert "DEBUG STUB INFO" in result["text"]


def test_extract_text_with_page_number():
    """Test OCR text extraction with page number."""
    image_data = b"fake png image data"
    result = extract_text_from_image(image_data, page_number=5)

    assert "Page 5" in result["text"]


def test_extract_text_with_filename():
    """Test OCR text extraction with PDF filename."""
    image_data = b"fake png image data"
    result = extract_text_from_image(image_data, pdf_filename="test.pdf")

    assert "test.pdf" in result["text"]


def test_extract_text_with_all_params():
    """Test OCR text extraction with all parameters."""
    image_data = b"fake png image data"
    result = extract_text_from_image(
        image_data, page_number=3, pdf_filename="document.pdf"
    )

    assert "Page 3" in result["text"]
    assert "document.pdf" in result["text"]
    assert result["engine"] == "stub"
    assert result["confidence"] == 1.0

