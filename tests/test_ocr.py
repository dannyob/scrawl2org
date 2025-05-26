"""Tests for OCR module."""

import os
from unittest.mock import patch

from scrawl2org.ocr import _extract_text_stub, extract_text_from_image


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


def test_extract_text_stub_function():
    """Test the stub OCR function directly."""
    image_data = b"fake png image data"
    result = _extract_text_stub(image_data, page_number=2, pdf_filename="test.pdf")

    assert isinstance(result, dict)
    assert "text" in result
    assert "Page 2" in result["text"]
    assert "test.pdf" in result["text"]
    assert result["engine"] == "stub"


@patch.dict(os.environ, {"SCRAWL2ORG_USE_LLM_OCR": "false"})
def test_extract_text_stub_mode():
    """Test OCR in stub mode (LLM disabled)."""
    image_data = b"fake png image data"
    result = extract_text_from_image(image_data)

    assert result["engine"] == "stub"
    assert "DEBUG STUB INFO" in result["text"]


@patch.dict(os.environ, {"SCRAWL2ORG_USE_LLM_OCR": "true"})
@patch("scrawl2org.ocr.extract_text_from_image_llm")
def test_extract_text_llm_mode_success(mock_llm_ocr):
    """Test OCR in LLM mode when successful."""
    # Setup mock LLM response
    mock_llm_ocr.return_value = {
        "text": "LLM extracted text",
        "confidence": 0.95,
        "engine": "llm",
        "model": "gemini-1.5-flash-latest",
    }

    image_data = b"fake png image data"
    result = extract_text_from_image(image_data, page_number=1, pdf_filename="test.pdf")

    assert result["engine"] == "llm"
    assert result["text"] == "LLM extracted text"
    mock_llm_ocr.assert_called_once_with(
        image_data,
        page_number=1,
        pdf_filename="test.pdf",
        model_name="gemini-1.5-flash-latest",
    )


@patch.dict(
    os.environ,
    {"SCRAWL2ORG_USE_LLM_OCR": "true", "SCRAWL2ORG_LLM_MODEL": "claude-3-haiku"},
)
@patch("scrawl2org.ocr.extract_text_from_image_llm")
def test_extract_text_llm_custom_model(mock_llm_ocr):
    """Test OCR with custom LLM model."""
    mock_llm_ocr.return_value = {
        "text": "Claude extracted text",
        "confidence": 0.92,
        "engine": "llm",
        "model": "claude-3-haiku",
    }

    image_data = b"fake png image data"
    extract_text_from_image(image_data)

    mock_llm_ocr.assert_called_once_with(
        image_data, page_number=None, pdf_filename=None, model_name="claude-3-haiku"
    )


@patch.dict(os.environ, {"SCRAWL2ORG_USE_LLM_OCR": "true"})
@patch("scrawl2org.ocr.extract_text_from_image_llm")
@patch("builtins.print")
def test_extract_text_llm_fallback_to_stub(mock_print, mock_llm_ocr):
    """Test OCR fallback to stub when LLM fails."""
    # Setup mock LLM to fail
    mock_llm_ocr.side_effect = Exception("LLM connection failed")

    image_data = b"fake png image data"
    result = extract_text_from_image(image_data)

    # Should fall back to stub
    assert result["engine"] == "stub"
    assert "DEBUG STUB INFO" in result["text"]

    # Should print error message
    mock_print.assert_called_once()
    assert "LLM OCR failed" in mock_print.call_args[0][0]
