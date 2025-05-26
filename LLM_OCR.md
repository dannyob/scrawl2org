# LLM-based OCR Feature

This document describes the LLM-based OCR functionality in scrawl2org, which uses vision-capable language models to extract and process text from PDF page images.

## Overview

The LLM OCR feature leverages Simon Willison's [LLM library](https://llm.datasette.io/) to analyze page images using state-of-the-art vision language models. Instead of traditional OCR tools, it uses models like GPT-4o, Claude 3, or Gemini to:

1. **Extract text** from images with high accuracy
2. **Convert to markdown** format with proper structure  
3. **Handle complex layouts** including tables, lists, and formatting
4. **Embed illustrations** as SVG content when text is unreadable
5. **Provide contextual understanding** of the document content

## Setup

### 1. Install Dependencies

The LLM library is automatically installed as a dependency. Ensure you have access to a vision-capable model:

```bash
# Install additional models if needed
llm install llm-claude-3
llm install llm-gemini
```

### 2. Configure API Keys

Set up API keys for your chosen model:

```bash
# For OpenAI models (default)
llm keys set openai
# Enter your API key when prompted

# For Claude models  
llm keys set claude
# Enter your Anthropic API key

# For Gemini models
llm keys set gemini
# Enter your Google API key
```

### 3. Test Connection

Verify your setup:

```bash
# Test basic connection
llm "Hello, this is a test"

# Test vision capabilities
llm "Describe this image" -a path/to/test-image.jpg
```

## Usage

### Command Line Options

Enable LLM-based OCR using these CLI flags:

```bash
# Enable LLM OCR with default model (gemini-1.5-flash-latest)
scrawl2org document.pdf --use-llm-ocr

# Use a specific model
scrawl2org document.pdf --use-llm-ocr --llm-model claude-3-haiku

# Combine with other options
scrawl2org document.pdf --use-llm-ocr --llm-model gpt-4o --verbose
```

### Environment Variables

You can also configure LLM OCR via environment variables:

```bash
# Enable LLM OCR
export SCRAWL2ORG_USE_LLM_OCR=true

# Set model (optional)
export SCRAWL2ORG_LLM_MODEL=claude-3-sonnet

# Run processing
scrawl2org document.pdf
```

### Supported Models

Common vision-capable models include:

- **OpenAI**: `gpt-4o`, `gpt-4o-mini`
- **Google**: `gemini-1.5-flash-latest` (default), `gemini-pro-vision`, `gemini-1.5-pro`
- **Anthropic**: `claude-3-haiku`, `claude-3-sonnet`, `claude-3-opus`
- **Local**: Various models via Ollama (e.g., `llava`, `qwen2-vl`)

## Output Format

The LLM OCR produces structured markdown output:

```markdown
# Document Title

## Section 1

This is extracted text with **formatting** preserved.

- Bullet points are maintained
- Lists are properly structured

| Table | Headers | Work |
|-------|---------|------|
| Data  | Is      | Extracted |

### Illustrations

When parts of the image contain illustrations or are unreadable, they are embedded as SVG:

<svg width="100" height="50">
  <text x="10" y="30">Illustration placeholder</text>
</svg>
```

## Programming API

Use LLM OCR programmatically:

```python
from scrawl2org.llm_ocr import extract_text_from_image_llm

# Basic usage
result = extract_text_from_image_llm(image_data)
print(result['text'])

# With custom model
result = extract_text_from_image_llm(
    image_data,
    model_name="claude-3-sonnet",
    page_number=1,
    pdf_filename="document.pdf"
)

# Check available models
from scrawl2org.llm_ocr import list_available_vision_models
models = list_available_vision_models()
print(f"Available models: {models}")
```

## Configuration

### Model Selection

Choose models based on your needs:

- **Speed**: `gemini-1.5-flash-latest`, `gpt-4o-mini`, `claude-3-haiku` (fastest, cheapest)
- **Quality**: `gpt-4o`, `claude-3-sonnet` (balanced)
- **Precision**: `claude-3-opus`, `gpt-4o` (highest quality)
- **Local**: Ollama models (private, offline)

### Error Handling

The system includes robust fallback:

1. **Primary**: LLM-based OCR (when enabled)
2. **Fallback**: Stub implementation (for testing)
3. **Future**: Traditional OCR tools (tesseract, etc.)

If LLM processing fails, the system automatically falls back to the stub implementation and logs the error.

## Troubleshooting

### Common Issues

**"Model does not support image attachments"**
- Ensure you're using a vision-capable model
- Try: `gemini-1.5-flash-latest`, `gpt-4o-mini`, `claude-3-haiku`, or `gemini-pro-vision`

**API Key Errors**  
- Verify API key is set: `llm keys list`
- Check key permissions and billing status

**Connection Failures**
- Test basic connectivity: `llm "test"`
- Check internet connection and API status

**High Costs**
- Use smaller models: `gemini-1.5-flash-latest`, `gpt-4o-mini` instead of `gpt-4o`
- Consider local models via Ollama
- Monitor usage: check API dashboard

### Debug Mode

Enable verbose logging:

```bash
scrawl2org document.pdf --use-llm-ocr --verbose
```

Test LLM connection:

```python
from scrawl2org.llm_ocr import test_llm_connection
if test_llm_connection("gemini-1.5-flash-latest"):
    print("✓ Connection successful")
else:
    print("✗ Connection failed")
```

## Performance

### Speed Comparison

- **Traditional OCR**: ~100ms per page
- **LLM OCR**: ~2-5 seconds per page  
- **Quality**: LLM significantly better for complex layouts

### Cost Considerations

LLM OCR uses API calls, which have costs:

- **gemini-1.5-flash-latest**: ~$0.005 per page (cheapest)
- **gpt-4o-mini**: ~$0.01 per page
- **claude-3-haiku**: ~$0.005 per page
- **Local models**: Free after setup

Budget-friendly options:
1. Use smaller models (`gemini-1.5-flash-latest`, `gpt-4o-mini`, `claude-3-haiku`)
2. Process only key pages
3. Set up local models with Ollama

## Future Enhancements

Planned improvements:

- **Batch processing** for multiple pages
- **Custom prompts** for specific document types  
- **Output format options** (plain text, structured data)
- **Local model integration** with better Ollama support
- **Hybrid approaches** combining LLM + traditional OCR