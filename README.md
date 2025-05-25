# scrawl2org

Extract PDF pages as images and store them in SQLite database with intelligent change detection.

## Overview

`scrawl2org` is a Python command-line tool that processes PDF files and extracts each page as a PNG image, storing them in a SQLite database. It uses hash-based change detection to efficiently handle repeated processing of the same PDF files, only updating images when the source PDF or individual pages have changed.

## Features

- **Efficient Change Detection**: Uses SHA-256 hashes to detect changes at both file and page level
- **SQLite Storage**: Stores images as BLOBs with metadata (filename, page number, timestamps, hashes)
- **Incremental Updates**: Only processes changed pages, skipping unchanged content
- **CLI Interface**: Simple command-line interface with options for database path, force updates, and verbose output
- **Automatic Cleanup**: Removes page images when PDF page count decreases

## Installation

### Using uv (recommended)

```bash
# Install locally in development mode
make install

# Install globally as a tool
make install-tool

# Or install directly with uv
uv tool install .
```

### Using pip

```bash
pip install -e .
```

## Usage

### Basic Usage

```bash
# Process a PDF file
scrawl2org document.pdf

# Use custom database location
scrawl2org document.pdf --database /path/to/custom.db

# Force reprocessing even if unchanged
scrawl2org document.pdf --force

# Verbose output
scrawl2org document.pdf --verbose
```

### Advanced Usage

```bash
# Process with all options
scrawl2org document.pdf -d custom.db -f -v
```

## Database Schema

The tool creates two tables:

### `pdf_files`
- `id`: Primary key
- `filename`: Full path to PDF file
- `file_hash`: SHA-256 hash of PDF content
- `last_processed`: Timestamp of last processing

### `page_images`
- `id`: Primary key
- `pdf_file_id`: Foreign key to pdf_files
- `page_number`: Page number (0-based)
- `image_data`: PNG image data (BLOB)
- `image_hash`: SHA-256 hash of image data
- `last_updated`: Timestamp of last update

See [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) for complete schema documentation.

## Development

### Running Tests

```bash
# Run all tests
make test

# Run tests with coverage
make test-coverage
```

### Code Quality

```bash
# Run linting (if ruff available)
make lint

# Format code (if ruff available)
make format
```

### Building

```bash
# Clean build artifacts
make clean

# Install development dependencies
make install-dev
```

## Dependencies

- **Python 3.8+**
- **PyMuPDF**: PDF processing and image extraction
- **Click**: Command-line interface
- **pytest**: Testing framework (dev dependency)

## How It Works

1. **File Change Detection**: Calculates SHA-256 hash of input PDF
2. **Database Lookup**: Checks if file exists and hash has changed
3. **Page Processing**: Extracts each page as 2x scaled PNG image
4. **Image Comparison**: Compares image hashes to detect page-level changes
5. **Storage**: Updates only changed images in SQLite database
6. **Cleanup**: Removes images for pages that no longer exist

## License

See [LICENSE](LICENSE) file for details.
