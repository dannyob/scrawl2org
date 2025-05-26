"""LLM-based OCR functionality using Simon Willison's LLM library."""

import re
import sys
import time
from typing import Any, Dict

import llm


def _extract_markdown_content(response_text: str) -> str:
    """Extract text content from between ```markdown and ``` delimiters.

    Args:
        response_text: Full LLM response text

    Returns:
        Extracted markdown content (without delimiters), or empty string if no delimiters found
    """
    # Look for ```markdown ... ``` pattern
    markdown_pattern = r"```markdown\s*\n(.*?)\n```"
    match = re.search(markdown_pattern, response_text, re.DOTALL | re.IGNORECASE)

    if match:
        return match.group(1).strip()

    # Fallback: look for any ``` ... ``` pattern
    code_pattern = r"```\s*\n(.*?)\n```"
    match = re.search(code_pattern, response_text, re.DOTALL)

    if match:
        return match.group(1).strip()

    # If no markdown delimiters found, warn to stderr and return empty string
    print(
        f"Warning: LLM response did not contain markdown delimiters. "
        f"Response was: {response_text[:100]}{'...' if len(response_text) > 100 else ''}",
        file=sys.stderr,
    )
    return ""


def extract_text_from_image_llm(
    image_data: bytes,
    page_number: int = None,
    pdf_filename: str = None,
    model_name: str = "gemini-1.5-flash-latest",
    api_key: str = None,
) -> Dict[str, Any]:
    """Extract text from page image using LLM vision capabilities.

    This function uses Simon Willison's LLM library to analyze images and extract
    text content, converting it to markdown format with SVG embedding for
    illustrations or unreadable parts.

    Args:
        image_data: PNG image data as bytes
        page_number: Page number (optional, for logging/debugging)
        pdf_filename: PDF filename (optional, for logging/debugging)
        model_name: LLM model to use (default: gpt-4o-mini)
        api_key: Optional API key override

    Returns:
        Dictionary containing OCR results with at least a 'text' field

    Raises:
        Exception: If LLM processing fails or model is not available
    """
    start_time = time.time()

    try:
        # Get the specified model
        model = llm.get_model(model_name)

        # Check if model supports vision/attachments
        if not hasattr(model, "attachment_types") or not model.attachment_types:
            raise ValueError(f"Model {model_name} does not support image attachments")

        # Prepare the prompt that emulates the CLI command:
        # llm -x -a <image-data> "Turn this into markdown text..."
        prompt = (
            "Turn this into markdown text, demarcated by the ```markdown code tag. "
            "If there are parts of the text which appear to be illustrations or "
            "unreadable, embed them as SVG content. "
            "If this is a blank page with no text content, just return an empty ```markdown region."
        )

        # Create attachment from binary image data
        attachment = llm.Attachment(content=image_data)

        # Execute the prompt with image attachment
        response = model.prompt(
            prompt,
            attachments=[attachment],
            key=api_key,  # Optional API key override
        )

        # Extract the response text
        response_text = response.text()

        # Extract text from between ```markdown and ``` delimiters
        extracted_text = _extract_markdown_content(response_text)

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Build metadata info
        debug_info = f"LLM OCR using {model_name}"
        if page_number is not None:
            debug_info += f" - Page {page_number}"
        if pdf_filename:
            debug_info += f" from {pdf_filename}"

        return {
            "text": extracted_text,
            "confidence": 1.0,  # LLM doesn't provide confidence scores
            "processing_time_ms": processing_time_ms,
            "engine": "llm",
            "model": model_name,
            "version": "1.0.0",
            "metadata": {
                "prompt_used": prompt,
                "response_length": len(extracted_text),
                "debug_info": debug_info,
            },
        }

    except Exception as e:
        # If LLM processing fails, provide error information
        processing_time_ms = int((time.time() - start_time) * 1000)

        error_info = f"LLM OCR failed with {model_name}: {str(e)}"
        if page_number is not None:
            error_info += f" - Page {page_number}"
        if pdf_filename:
            error_info += f" from {pdf_filename}"

        return {
            "text": f"[LLM OCR Error: {str(e)}]",
            "confidence": 0.0,
            "processing_time_ms": processing_time_ms,
            "engine": "llm",
            "model": model_name,
            "version": "1.0.0",
            "error": str(e),
            "metadata": {
                "error_info": error_info,
                "failed": True,
            },
        }


def list_available_vision_models() -> list[str]:
    """List all available LLM models that support vision/image attachments.

    Returns:
        List of model names that support image processing
    """
    available_models = []

    try:
        # Get all available models
        models = llm.get_models()

        for model in models:
            # Check if model supports attachments (vision)
            if hasattr(model, "attachment_types") and model.attachment_types:
                # Check if it supports image types
                image_types = {"image/jpeg", "image/png", "image/webp", "image/gif"}
                if any(img_type in model.attachment_types for img_type in image_types):
                    available_models.append(model.model_id)

    except Exception:
        # If we can't enumerate models, return common vision models
        available_models = [
            "gpt-4o-mini",
            "gpt-4o",
            "claude-3-haiku",
            "claude-3-sonnet",
            "claude-3-opus",
            "gemini-pro-vision",
        ]

    return available_models


def test_llm_connection(model_name: str = "gpt-4o-mini") -> bool:
    """Test if LLM connection is working with the specified model.

    Args:
        model_name: Model to test (default: gpt-4o-mini)

    Returns:
        True if connection successful, False otherwise
    """
    try:
        model = llm.get_model(model_name)

        # Try a simple prompt (without image) to test connection
        response = model.prompt("Hello, just testing connection. Reply with 'OK'.")

        return "OK" in response.text().upper()

    except Exception:
        return False
