"""Tests for extractor module."""

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from scrawl2org.extractor import ImageExtractor


@pytest.fixture
def temp_db_path():
    """Create a temporary database path for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    yield db_path

    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


def test_parse_page_range_single_page():
    """Test parsing single page number."""
    extractor = ImageExtractor()

    result = extractor.parse_page_range("5")
    assert result == {5}


def test_parse_page_range_range():
    """Test parsing page range."""
    extractor = ImageExtractor()

    result = extractor.parse_page_range("1-3")
    assert result == {1, 2, 3}


def test_parse_page_range_multiple_single():
    """Test parsing multiple single pages."""
    extractor = ImageExtractor()

    result = extractor.parse_page_range("1,3,5")
    assert result == {1, 3, 5}


def test_parse_page_range_mixed():
    """Test parsing mixed ranges and single pages."""
    extractor = ImageExtractor()

    result = extractor.parse_page_range("1-3,5,7-9")
    assert result == {1, 2, 3, 5, 7, 8, 9}


def test_parse_page_range_with_spaces():
    """Test parsing with spaces."""
    extractor = ImageExtractor()

    result = extractor.parse_page_range(" 1 - 3 , 5 , 7 - 9 ")
    assert result == {1, 2, 3, 5, 7, 8, 9}


def test_parse_page_range_invalid_range():
    """Test parsing invalid range."""
    extractor = ImageExtractor()

    with pytest.raises(ValueError, match="Invalid page number"):
        extractor.parse_page_range("1-")

    with pytest.raises(ValueError, match="Invalid page number"):
        extractor.parse_page_range("a-b")


def test_parse_page_range_invalid_single():
    """Test parsing invalid single page."""
    extractor = ImageExtractor()

    with pytest.raises(ValueError, match="Invalid page number"):
        extractor.parse_page_range("abc")


def test_parse_page_range_zero_page():
    """Test parsing page number zero."""
    extractor = ImageExtractor()

    with pytest.raises(ValueError, match="Page numbers must be >= 1"):
        extractor.parse_page_range("0")


def test_parse_page_range_negative_page():
    """Test parsing negative page number."""
    extractor = ImageExtractor()

    with pytest.raises(ValueError, match="Page numbers must be >= 1"):
        extractor.parse_page_range("-1")


def test_parse_page_range_reverse_range():
    """Test parsing reverse range."""
    extractor = ImageExtractor()

    with pytest.raises(ValueError, match="Invalid range: start"):
        extractor.parse_page_range("5-3")


def test_parse_page_range_empty():
    """Test parsing empty string."""
    extractor = ImageExtractor()

    with pytest.raises(ValueError, match="No valid page numbers"):
        extractor.parse_page_range("")


@patch("scrawl2org.extractor.ImageExtractor._output_image")
def test_extract_pages_single_page(mock_output, temp_db_path):
    """Test extracting single page."""
    extractor = ImageExtractor(temp_db_path)

    # Mock database methods
    extractor.db.get_pdf_file_id = MagicMock(return_value=1)
    extractor.db.get_page_image = MagicMock(return_value=b"fake image data")

    extractor.extract_pages("test.pdf", "2", "output.png")

    # Verify database calls
    extractor.db.get_pdf_file_id.assert_called_once_with("test.pdf")
    extractor.db.get_page_image.assert_called_once_with(1, 1)  # 0-based page number

    # Verify output
    mock_output.assert_called_once_with(b"fake image data", "output.png", 2, {})


@patch("scrawl2org.extractor.KittyImageDisplay.is_kitty_terminal", return_value=False)
def test_extract_pages_multiple_pages_stdout(mock_kitty_check, temp_db_path):
    """Test extracting multiple pages to stdout raises error in non-Kitty terminals."""
    extractor = ImageExtractor(temp_db_path)

    # Mock database methods
    extractor.db.get_pdf_file_id = MagicMock(return_value=1)

    with pytest.raises(ValueError, match="Multiple pages cannot be output to stdout"):
        extractor.extract_pages("test.pdf", "1-3", None)


@patch("scrawl2org.extractor.ImageExtractor._output_image")
def test_extract_pages_multiple_pages_to_files(mock_output, temp_db_path):
    """Test extracting multiple pages to numbered files."""
    extractor = ImageExtractor(temp_db_path)

    # Mock database methods
    extractor.db.get_pdf_file_id = MagicMock(return_value=1)
    extractor.db.get_page_image = MagicMock(
        side_effect=[b"page1 data", b"page2 data", b"page3 data"]
    )

    extractor.extract_pages("test.pdf", "1-3", "output.png")

    # Verify database calls
    extractor.db.get_pdf_file_id.assert_called_once_with("test.pdf")
    assert extractor.db.get_page_image.call_count == 3

    # Verify output calls with numbered filenames
    expected_calls = [
        (b"page1 data", "output_page001.png", 1, {}),
        (b"page2 data", "output_page002.png", 2, {}),
        (b"page3 data", "output_page003.png", 3, {}),
    ]
    actual_calls = [call[0] for call in mock_output.call_args_list]
    assert actual_calls == expected_calls


def test_extract_pages_pdf_not_found(temp_db_path):
    """Test extracting from non-existent PDF."""
    extractor = ImageExtractor(temp_db_path)

    # Mock database methods
    extractor.db.get_pdf_file_id = MagicMock(return_value=None)

    with pytest.raises(ValueError, match="PDF file not found"):
        extractor.extract_pages("nonexistent.pdf", "1")


def test_extract_pages_page_not_found(temp_db_path):
    """Test extracting non-existent page."""
    extractor = ImageExtractor(temp_db_path)

    # Mock database methods
    extractor.db.get_pdf_file_id = MagicMock(return_value=1)
    extractor.db.get_page_image = MagicMock(return_value=None)

    with pytest.raises(ValueError, match="Page 1 not found"):
        extractor.extract_pages("test.pdf", "1")


@patch("builtins.open")
@patch("sys.stderr")
def test_output_image_to_file(mock_stderr, mock_open):
    """Test outputting image to file."""
    extractor = ImageExtractor()
    mock_file = MagicMock()
    mock_open.return_value.__enter__.return_value = mock_file

    extractor._output_image(b"image data", "output.png")

    mock_open.assert_called_once_with("output.png", "wb")
    mock_file.write.assert_called_once_with(b"image data")


@patch("scrawl2org.extractor.KittyImageDisplay.is_kitty_terminal", return_value=False)
@patch("sys.stdout")
def test_output_image_to_stdout(mock_stdout, mock_kitty_check):
    """Test outputting image to stdout (non-Kitty terminal)."""
    extractor = ImageExtractor()
    mock_stdout.buffer = MagicMock()

    extractor._output_image(b"image data", None)

    mock_stdout.buffer.write.assert_called_once_with(b"image data")


@patch("scrawl2org.extractor.KittyImageDisplay.display_image_inline")
@patch("scrawl2org.extractor.KittyImageDisplay.is_kitty_terminal", return_value=True)
@patch("sys.stderr")
def test_output_image_to_kitty_terminal(mock_stderr, mock_kitty_check, mock_display):
    """Test outputting image to stdout (Kitty terminal)."""
    extractor = ImageExtractor()

    extractor._output_image(b"image data", None, 5)

    mock_display.assert_called_once_with(b"image data", "page_5")
