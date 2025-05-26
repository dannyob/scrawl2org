"""Tests for kitty_display module."""

import os
from unittest.mock import patch

from scrawl2org.kitty_display import KittyImageDisplay


def test_is_kitty_terminal_with_term():
    """Test detection via TERM environment variable."""
    with patch.dict(os.environ, {"TERM": "xterm-kitty"}):
        assert KittyImageDisplay.is_kitty_terminal() is True


def test_is_kitty_terminal_with_window_id():
    """Test detection via KITTY_WINDOW_ID environment variable."""
    with patch.dict(os.environ, {"KITTY_WINDOW_ID": "123"}):
        assert KittyImageDisplay.is_kitty_terminal() is True


def test_is_kitty_terminal_false():
    """Test detection when not in Kitty terminal."""
    with patch.dict(os.environ, {}, clear=True):
        assert KittyImageDisplay.is_kitty_terminal() is False


@patch("builtins.print")
@patch("sys.stdout")
def test_display_image_single_chunk(mock_stdout, mock_print):
    """Test displaying image that fits in single chunk."""
    image_data = b"small image data"

    KittyImageDisplay.display_image(image_data, "test.png")

    # Should write escape sequence and print newline
    assert mock_stdout.write.call_count == 1
    assert mock_stdout.flush.call_count == 1
    mock_print.assert_called_once()

    # Check the escape sequence format
    written_data = mock_stdout.write.call_args[0][0]
    assert written_data.startswith("\x1b_G")
    assert written_data.endswith("\x1b\\")
    assert "a=T" in written_data  # action=transmit
    assert "f=100" in written_data  # format=PNG


@patch("builtins.print")
@patch("sys.stdout")
def test_display_image_with_dimensions(mock_stdout, mock_print):
    """Test displaying image with specific dimensions."""
    image_data = b"test image"

    KittyImageDisplay.display_image(image_data, "test.png", width=40, height=20)

    written_data = mock_stdout.write.call_args[0][0]
    assert "c=40" in written_data  # columns
    assert "r=20" in written_data  # rows


@patch("builtins.print")
@patch("sys.stdout")
def test_display_image_multiple_chunks(mock_stdout, mock_print):
    """Test displaying large image requiring multiple chunks."""
    # Create image data larger than chunk size
    large_data = b"x" * 5000  # Larger than 4096 chunk size

    KittyImageDisplay.display_image(large_data)

    # Should have multiple write calls for chunks (plus print call)
    assert mock_stdout.write.call_count > 1

    # First chunk should have m=1 (more chunks)
    first_call = mock_stdout.write.call_args_list[0][0][0]
    assert ",m=1;" in first_call

    # Final chunk should have m=0 (no more chunks)
    chunk_calls = [
        call
        for call in mock_stdout.write.call_args_list
        if call[0][0].startswith("\x1b_G")
    ]
    last_chunk_call = chunk_calls[-1][0][0]
    assert "m=0;" in last_chunk_call


@patch("builtins.print")
@patch("sys.stdout")
def test_display_image_inline(mock_stdout, mock_print):
    """Test inline image display."""
    image_data = b"test data"

    KittyImageDisplay.display_image_inline(image_data, "test.png")

    # Should call display_image and print newline
    mock_stdout.write.assert_called()
    mock_print.assert_called_once()


@patch("builtins.print")
@patch("sys.stdout")
def test_display_image_sized(mock_stdout, mock_print):
    """Test sized image display."""
    image_data = b"test data"

    KittyImageDisplay.display_image_sized(image_data, 30, 15, "test.png")

    written_data = mock_stdout.write.call_args[0][0]
    assert "c=30" in written_data
    assert "r=15" in written_data
