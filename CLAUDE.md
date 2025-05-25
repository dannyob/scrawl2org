# Claude Code Memory

## Project: scrawl2org

### Overview
Python CLI tool that extracts PDF pages as images and stores them in SQLite database with hash-based change detection.

### Project Structure
```
scrawl2org/
├── scrawl2org/              # Main package
│   ├── __init__.py         # Package initialization
│   ├── main.py             # CLI entry point with Click
│   ├── processor.py        # PDF processing with PyMuPDF
│   └── database.py         # SQLite operations and hash management
├── tests/                  # Unit tests
│   ├── test_main.py        # CLI tests
│   ├── test_processor.py   # PDF processing tests
│   └── test_database.py    # Database operation tests
├── pyproject.toml          # uv/pip configuration
├── Makefile               # Development commands
├── DATABASE_SCHEMA.md     # Database documentation
└── README.md              # User documentation
```

### Key Components

#### CLI (main.py)
- Uses Click for argument parsing
- Entry point: `scrawl2org <pdf_file> [options]`
- Options: `--database`, `--force`, `--verbose`
- Installed as executable via `pyproject.toml` scripts section

#### PDF Processing (processor.py)
- Uses PyMuPDF (fitz) for PDF manipulation
- Extracts pages as PNG images with 2x scaling
- Implements change detection via file/image hashes
- Handles page cleanup when PDF shrinks

#### Database (database.py)
- Two-table schema: `pdf_files` and `page_images`
- SHA-256 hashing for change detection
- Foreign key relationships with proper indexing
- Automatic table creation and maintenance

### Development Commands
```bash
make test           # Run pytest tests
make test-coverage  # Run tests with coverage
make install        # Install in development mode
make install-tool   # Install globally with uv tool
make lint          # Run ruff linting (if available)
make format        # Format code with ruff (if available)
make clean         # Clean build artifacts
```

### Testing
- 22 unit tests with comprehensive coverage
- Mocked PyMuPDF dependencies for isolation
- Temporary file fixtures for database and PDF testing
- Tests all CLI options and error conditions

### Dependencies
- **Runtime**: PyMuPDF (PDF processing), Click (CLI)
- **Development**: pytest, pytest-cov
- **Python**: 3.8+ required

### Database Schema
- `pdf_files`: filename, file_hash, last_processed
- `page_images`: pdf_file_id, page_number, image_data (BLOB), image_hash, last_updated
- Indexes on (pdf_file_id, page_number) and image_hash

### Hash-based Change Detection
1. Calculate SHA-256 of entire PDF file
2. Compare with stored hash to detect file changes
3. For each page, calculate SHA-256 of PNG image data
4. Update only changed pages in database
5. Clean up pages that no longer exist

### Build System
- Uses `uv` as package manager and build tool
- Configured in `pyproject.toml` with proper entry points
- Can install locally (`uv pip install -e .`) or globally (`uv tool install .`)

### Known Issues
- PyMuPDF shows deprecation warnings (harmless)
- Path resolution differs on macOS (/private/var vs /var) - handled in tests

### Usage Examples
```bash
# Basic usage
scrawl2org document.pdf

# Custom database and verbose output
scrawl2org document.pdf -d custom.db -v

# Force reprocessing
scrawl2org document.pdf --force
```