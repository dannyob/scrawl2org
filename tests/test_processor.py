"""Tests for processor module."""

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from scrawl2org.processor import PDFProcessor


@pytest.fixture
def temp_db_path():
    """Create a temporary database path for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    yield db_path

    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def sample_pdf():
    """Create a sample PDF file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        # Write minimal valid PDF content
        f.write(b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
        pdf_path = f.name

    yield pdf_path

    # Cleanup
    os.unlink(pdf_path)


def test_processor_initialization(temp_db_path):
    """Test PDFProcessor initialization."""
    processor = PDFProcessor(temp_db_path)
    assert processor.db.db_path == temp_db_path


def test_process_pdf_file_not_found(temp_db_path):
    """Test processing non-existent PDF file."""
    processor = PDFProcessor(temp_db_path)

    with pytest.raises(FileNotFoundError):
        processor.process_pdf("/nonexistent/file.pdf")


@patch("scrawl2org.processor.fitz")
def test_process_pdf_unchanged_file(mock_fitz, temp_db_path, sample_pdf):
    """Test processing unchanged PDF file."""
    processor = PDFProcessor(temp_db_path)

    # Mock the database to return unchanged file
    with patch.object(processor.db, "check_pdf_changed") as mock_check:
        mock_check.return_value = (False, 123)  # unchanged, existing file

        with patch("builtins.print") as mock_print:
            processor.process_pdf(sample_pdf)

            # Should skip processing
            # Check that print was called with a message containing "unchanged, skipping"
            mock_print.assert_called()
            call_args = mock_print.call_args[0][0]
            assert "PDF unchanged, skipping:" in call_args
            assert sample_pdf in call_args
            mock_fitz.open.assert_not_called()


@patch("scrawl2org.processor.fitz")
@patch("scrawl2org.processor.extract_text_from_image")
def test_process_pdf_new_file(mock_ocr, mock_fitz, temp_db_path, sample_pdf):
    """Test processing new PDF file."""
    # Setup mocks
    mock_doc = MagicMock()
    mock_doc.__len__.return_value = 2
    mock_doc.name = sample_pdf  # Add name attribute for OCR
    mock_page = MagicMock()
    mock_doc.__getitem__.return_value = mock_page
    mock_pix = MagicMock()
    mock_pix.tobytes.return_value = b"fake image data"
    mock_page.get_pixmap.return_value = mock_pix
    mock_fitz.open.return_value = mock_doc
    mock_fitz.Matrix.return_value = MagicMock()

    # Mock OCR
    mock_ocr.return_value = {"text": "Mock OCR result", "confidence": 0.9}

    processor = PDFProcessor(temp_db_path)

    # Process the PDF
    with patch("builtins.print"):
        processor.process_pdf(sample_pdf)

    # Verify PDF was opened and processed
    mock_fitz.open.assert_called_once()
    mock_doc.close.assert_called_once()
    # Verify OCR was called for each page
    assert mock_ocr.call_count == 2


@patch("scrawl2org.processor.fitz")
def test_process_pdf_force_update(mock_fitz, temp_db_path, sample_pdf):
    """Test force processing unchanged PDF file."""
    # Setup mocks
    mock_doc = MagicMock()
    mock_doc.__len__.return_value = 1
    mock_page = MagicMock()
    mock_doc.__getitem__.return_value = mock_page
    mock_pix = MagicMock()
    mock_pix.tobytes.return_value = b"fake image data"
    mock_page.get_pixmap.return_value = mock_pix
    mock_fitz.open.return_value = mock_doc
    mock_fitz.Matrix.return_value = MagicMock()

    processor = PDFProcessor(temp_db_path)

    # Mock the database to return unchanged file
    with patch.object(processor.db, "check_pdf_changed") as mock_check:
        mock_check.return_value = (False, 123)  # unchanged, existing file

        with patch("builtins.print"):
            processor.process_pdf(sample_pdf, force_update=True)

        # Should still process despite being unchanged
        mock_fitz.open.assert_called_once()


@patch("scrawl2org.processor.fitz")
def test_get_page_count(mock_fitz, temp_db_path):
    """Test getting page count from PDF."""
    mock_doc = MagicMock()
    mock_doc.__len__.return_value = 5
    mock_fitz.open.return_value = mock_doc

    processor = PDFProcessor(temp_db_path)
    count = processor.get_page_count("dummy.pdf")

    assert count == 5
    mock_fitz.open.assert_called_once_with("dummy.pdf")
    mock_doc.close.assert_called_once()


@patch("scrawl2org.processor.fitz")
def test_extract_page_image(mock_fitz, temp_db_path):
    """Test extracting single page image."""
    mock_doc = MagicMock()
    mock_doc.__len__.return_value = 3
    mock_page = MagicMock()
    mock_doc.__getitem__.return_value = mock_page
    mock_pix = MagicMock()
    mock_pix.tobytes.return_value = b"extracted image data"
    mock_page.get_pixmap.return_value = mock_pix
    mock_fitz.open.return_value = mock_doc
    mock_fitz.Matrix.return_value = MagicMock()

    processor = PDFProcessor(temp_db_path)
    image_data = processor.extract_page_image("dummy.pdf", 1)

    assert image_data == b"extracted image data"
    mock_doc.__getitem__.assert_called_once_with(1)
    mock_doc.close.assert_called_once()


@patch("scrawl2org.processor.fitz")
def test_extract_page_image_invalid_page(mock_fitz, temp_db_path):
    """Test extracting image from invalid page number."""
    mock_doc = MagicMock()
    mock_doc.__len__.return_value = 2
    mock_fitz.open.return_value = mock_doc

    processor = PDFProcessor(temp_db_path)

    with pytest.raises(ValueError, match="Page 5 does not exist"):
        processor.extract_page_image("dummy.pdf", 5)

    mock_doc.close.assert_called_once()


@patch("scrawl2org.processor.extract_text_from_image")
@patch("scrawl2org.processor.fitz")
def test_process_page_stderr_output(
    mock_fitz, mock_ocr, temp_db_path, sample_pdf, capsys
):
    """Test that processing a page outputs status to stderr."""
    # Setup mocks
    mock_doc = MagicMock()
    mock_doc.name = sample_pdf
    mock_doc.__len__.return_value = 1
    mock_page = MagicMock()
    mock_doc.__getitem__.return_value = mock_page
    mock_pix = MagicMock()
    mock_pix.tobytes.return_value = b"fake image data"
    mock_page.get_pixmap.return_value = mock_pix
    mock_fitz.open.return_value = mock_doc
    mock_fitz.Matrix.return_value = MagicMock()

    # Mock OCR with text result
    mock_ocr.return_value = {"text": "Sample OCR text from page", "confidence": 0.9}

    processor = PDFProcessor(temp_db_path)

    # Process PDF and capture stderr using capsys
    processor.process_pdf(sample_pdf, force_update=True)

    # Get captured stderr (and stdout)
    captured = capsys.readouterr()
    stderr_output = captured.err

    # Verify stderr contains processing status
    assert "Page 1: processing..." in stderr_output
    assert "Page 1: completed OCR" in stderr_output
    assert "OCR text: Sample OCR text from page" in stderr_output


@patch("scrawl2org.processor.extract_text_from_image")
@patch("scrawl2org.processor.fitz")
def test_process_page_stderr_no_text(
    mock_fitz, mock_ocr, temp_db_path, sample_pdf, capsys
):
    """Test stderr output when OCR finds no text."""
    # Setup mocks
    mock_doc = MagicMock()
    mock_doc.name = sample_pdf
    mock_doc.__len__.return_value = 1
    mock_page = MagicMock()
    mock_doc.__getitem__.return_value = mock_page
    mock_pix = MagicMock()
    mock_pix.tobytes.return_value = b"fake image data"
    mock_page.get_pixmap.return_value = mock_pix
    mock_fitz.open.return_value = mock_doc
    mock_fitz.Matrix.return_value = MagicMock()

    # Mock OCR with empty text result
    mock_ocr.return_value = {"text": "", "confidence": 0.0}

    processor = PDFProcessor(temp_db_path)

    # Process PDF and capture stderr using capsys
    processor.process_pdf(sample_pdf, force_update=True)

    # Get captured stderr
    captured = capsys.readouterr()
    stderr_output = captured.err

    # Verify stderr shows no text detected
    assert "Page 1: processing..." in stderr_output
    assert "Page 1: completed OCR" in stderr_output
    assert "OCR text: (no text detected)" in stderr_output
