# Makefile for scrawl2org

.PHONY: install test test-coverage clean lint lint-fix format format-fix format-check help setup-pre-commit

# Default target
help:
	@echo "Available targets:"
	@echo "  install       - Install globally as uv tool (force reinstall)"
	@echo "  test          - Run unit tests"
	@echo "  test-coverage - Run tests with coverage report"
	@echo "  lint          - Run linting checks"
	@echo "  lint-fix      - Fix linting issues automatically"
	@echo "  format        - Format code with ruff"
	@echo "  format-fix    - Format and fix linting in one command"
	@echo "  format-check  - Check formatting without making changes"
	@echo "  setup-pre-commit - Install pre-commit hooks"
	@echo "  clean         - Clean up build artifacts"
	@echo "  help          - Show this help message"

# Install the package globally as a tool (force reinstall)
install:
	uv tool install --force --reinstall .

# Run tests
test:
	uv run pytest tests/ -v

# Run tests with coverage
test-coverage:
	uv run pytest tests/ -v --cov=scrawl2org --cov-report=term-missing

# Run linting checks
lint:
	uv run ruff check scrawl2org/ tests/

# Fix linting issues automatically where possible
lint-fix:
	uv run ruff check --fix scrawl2org/ tests/

# Format code with ruff (replaces black + isort)
format:
	uv run ruff format scrawl2org/ tests/

# Format and fix linting in one command
format-fix: format lint-fix

# Check formatting without making changes
format-check:
	uv run ruff format --check scrawl2org/ tests/

# Setup pre-commit hooks (optional)
setup-pre-commit:
	@if command -v pre-commit >/dev/null 2>&1; then \
		pre-commit install; \
		echo "Pre-commit hooks installed"; \
	else \
		echo "pre-commit not available. Install with: pip install pre-commit"; \
	fi

# Clean up build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

