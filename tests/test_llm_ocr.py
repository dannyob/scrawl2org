"""Tests for LLM-based OCR module."""

from unittest.mock import Mock, patch

from scrawl2org.llm_ocr import (
    _extract_markdown_content,
    extract_text_from_image_llm,
    list_available_vision_models,
    test_llm_connection,
)


def test_extract_markdown_content(capsys):
    """Test markdown content extraction from LLM responses."""
    # Test with proper markdown delimiters
    response_with_markdown = """
Here's the extracted text:

```markdown
# Document Title

This is some extracted text from the document.

- Item 1
- Item 2
```

Hope this helps!
"""

    result = _extract_markdown_content(response_with_markdown)
    expected = "# Document Title\n\nThis is some extracted text from the document.\n\n- Item 1\n- Item 2"
    assert result == expected

    # Test with generic code block
    response_with_code = """
```
Some text without markdown label
```
"""

    result = _extract_markdown_content(response_with_code)
    assert result == "Some text without markdown label"

    # Test with no delimiters - should warn and return empty string
    plain_response = "Just plain text response"
    result = _extract_markdown_content(plain_response)
    assert result == ""

    # Check that warning was printed to stderr
    captured = capsys.readouterr()
    assert "Warning: LLM response did not contain markdown delimiters" in captured.err
    assert "Just plain text response" in captured.err

    # Test case insensitive markdown
    response_caps = """
```MARKDOWN
Capitalized markdown
```
"""
    result = _extract_markdown_content(response_caps)
    assert result == "Capitalized markdown"

    # Test empty markdown region
    empty_response = """
```markdown
```
"""
    result = _extract_markdown_content(empty_response)
    assert result == ""


@patch("scrawl2org.llm_ocr.llm")
def test_extract_text_llm_basic(mock_llm):
    """Test basic LLM OCR text extraction."""
    # Setup mocks
    mock_model = Mock()
    mock_model.attachment_types = {"image/png", "image/jpeg"}
    mock_response = Mock()
    mock_response.text.return_value = (
        "```markdown\n# Test Document\nThis is extracted text.\n```"
    )
    mock_model.prompt.return_value = mock_response
    mock_llm.get_model.return_value = mock_model
    mock_llm.Attachment.return_value = Mock()

    image_data = b"fake png image data"
    result = extract_text_from_image_llm(image_data)

    # Should return a dictionary with required fields
    assert isinstance(result, dict)
    assert "text" in result
    assert "confidence" in result
    assert "engine" in result
    assert "model" in result

    # Verify the extracted text
    assert "Test Document" in result["text"]
    assert result["engine"] == "llm"
    assert result["model"] == "gemini-1.5-flash-latest"

    # Verify LLM was called correctly
    mock_llm.get_model.assert_called_once_with("gemini-1.5-flash-latest")
    mock_model.prompt.assert_called_once()


@patch("scrawl2org.llm_ocr.llm")
def test_extract_text_llm_with_page_info(mock_llm):
    """Test LLM OCR with page number and filename."""
    # Setup mocks
    mock_model = Mock()
    mock_model.attachment_types = {"image/png"}
    mock_response = Mock()
    mock_response.text.return_value = "Extracted text content"
    mock_model.prompt.return_value = mock_response
    mock_llm.get_model.return_value = mock_model
    mock_llm.Attachment.return_value = Mock()

    image_data = b"fake png image data"
    result = extract_text_from_image_llm(
        image_data, page_number=5, pdf_filename="test.pdf"
    )

    assert "Page 5" in result["metadata"]["debug_info"]
    assert "test.pdf" in result["metadata"]["debug_info"]


@patch("scrawl2org.llm_ocr.llm")
def test_extract_text_llm_custom_model(mock_llm):
    """Test LLM OCR with custom model."""
    # Setup mocks
    mock_model = Mock()
    mock_model.attachment_types = {"image/png"}
    mock_response = Mock()
    mock_response.text.return_value = "Custom model response"
    mock_model.prompt.return_value = mock_response
    mock_llm.get_model.return_value = mock_model
    mock_llm.Attachment.return_value = Mock()

    image_data = b"fake png image data"
    result = extract_text_from_image_llm(image_data, model_name="claude-3-sonnet")

    assert result["model"] == "claude-3-sonnet"
    mock_llm.get_model.assert_called_once_with("claude-3-sonnet")


@patch("scrawl2org.llm_ocr.llm")
def test_extract_text_llm_no_vision_support(mock_llm):
    """Test LLM OCR when model doesn't support vision."""
    # Setup mock model without vision support
    mock_model = Mock()
    mock_model.attachment_types = set()  # No attachment support
    mock_llm.get_model.return_value = mock_model

    image_data = b"fake png image data"
    result = extract_text_from_image_llm(image_data)

    # Should return error result
    assert result["confidence"] == 0.0
    assert "error" in result
    assert "does not support image attachments" in result["error"]


@patch("scrawl2org.llm_ocr.llm")
def test_extract_text_llm_api_error(mock_llm):
    """Test LLM OCR when API call fails."""
    # Setup mock to raise exception
    mock_llm.get_model.side_effect = Exception("API connection failed")

    image_data = b"fake png image data"
    result = extract_text_from_image_llm(image_data)

    # Should return error result
    assert result["confidence"] == 0.0
    assert "error" in result
    assert "API connection failed" in result["error"]
    assert "[LLM OCR Error:" in result["text"]


@patch("scrawl2org.llm_ocr.llm")
def test_extract_text_llm_with_api_key(mock_llm):
    """Test LLM OCR with custom API key."""
    # Setup mocks
    mock_model = Mock()
    mock_model.attachment_types = {"image/png"}
    mock_response = Mock()
    mock_response.text.return_value = "Text with custom key"
    mock_model.prompt.return_value = mock_response
    mock_llm.get_model.return_value = mock_model
    mock_llm.Attachment.return_value = Mock()

    image_data = b"fake png image data"
    custom_key = "sk-custom-key-123"

    extract_text_from_image_llm(image_data, api_key=custom_key)

    # Verify the API key was passed
    call_args = mock_model.prompt.call_args
    assert call_args[1]["key"] == custom_key


@patch("scrawl2org.llm_ocr.llm")
def test_list_available_vision_models(mock_llm):
    """Test listing available vision models."""
    # Setup mock models
    vision_model = Mock()
    vision_model.model_id = "gpt-4o-mini"
    vision_model.attachment_types = {"image/png", "image/jpeg"}

    text_model = Mock()
    text_model.model_id = "gpt-3.5-turbo"
    text_model.attachment_types = set()  # No vision support

    another_vision_model = Mock()
    another_vision_model.model_id = "claude-3-sonnet"
    another_vision_model.attachment_types = {"image/webp", "image/png"}

    mock_llm.get_models.return_value = [vision_model, text_model, another_vision_model]

    models = list_available_vision_models()

    # Should return only vision-capable models
    assert "gpt-4o-mini" in models
    assert "claude-3-sonnet" in models
    assert "gpt-3.5-turbo" not in models


@patch("scrawl2org.llm_ocr.llm")
def test_list_available_vision_models_fallback(mock_llm):
    """Test listing vision models when enumeration fails."""
    # Setup mock to fail
    mock_llm.get_models.side_effect = Exception("Failed to get models")

    models = list_available_vision_models()

    # Should return fallback list
    assert "gpt-4o-mini" in models
    assert "claude-3-haiku" in models
    assert len(models) > 0


@patch("scrawl2org.llm_ocr.llm")
def test_llm_connection_success(mock_llm):
    """Test successful LLM connection test."""
    # Setup mocks
    mock_model = Mock()
    mock_response = Mock()
    mock_response.text.return_value = "OK, connection successful"
    mock_model.prompt.return_value = mock_response
    mock_llm.get_model.return_value = mock_model

    result = test_llm_connection()

    assert result is True
    mock_llm.get_model.assert_called_once_with("gpt-4o-mini")


@patch("scrawl2org.llm_ocr.llm")
def test_llm_connection_failure(mock_llm):
    """Test failed LLM connection test."""
    # Setup mock to fail
    mock_llm.get_model.side_effect = Exception("Connection failed")

    result = test_llm_connection()

    assert result is False


@patch("scrawl2org.llm_ocr.llm")
def test_llm_connection_custom_model(mock_llm):
    """Test LLM connection test with custom model."""
    # Setup mocks
    mock_model = Mock()
    mock_response = Mock()
    mock_response.text.return_value = "Everything is OK here"
    mock_model.prompt.return_value = mock_response
    mock_llm.get_model.return_value = mock_model

    result = test_llm_connection("claude-3-haiku")

    assert result is True
    mock_llm.get_model.assert_called_once_with("claude-3-haiku")
