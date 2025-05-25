# Makefile for scrawl2org

.PHONY: install test test-coverage clean lint format help install-tool uninstall-tool install-dev

# Default target
help:
	@echo "Available targets:"
	@echo "  install       - Install the package using uv"
	@echo "  install-dev   - Install with development dependencies"
	@echo "  install-tool  - Install globally as uv tool (force reinstall)"
	@echo "  uninstall-tool - Uninstall the global tool"
	@echo "  test          - Run unit tests"
	@echo "  test-coverage - Run tests with coverage report"
	@echo "  lint          - Run linting checks"
	@echo "  format        - Format code"
	@echo "  clean         - Clean up build artifacts"
	@echo "  help          - Show this help message"

# Install the package
install:
	uv pip install -e .

# Install in development mode with test dependencies
install-dev:
	uv pip install -e ".[dev]"

# Run tests
test:
	uv run pytest tests/ -v

# Run tests with coverage
test-coverage:
	uv run pytest tests/ -v --cov=scrawl2org --cov-report=term-missing

# Run linting (if ruff is available)
lint:
	@if command -v ruff >/dev/null 2>&1; then \
		uv run ruff check scrawl2org/; \
		uv run ruff check tests/; \
	else \
		echo "ruff not available, skipping lint check"; \
	fi

# Format code (if ruff is available)
format:
	@if command -v ruff >/dev/null 2>&1; then \
		uv run ruff format scrawl2org/; \
		uv run ruff format tests/; \
	else \
		echo "ruff not available, skipping formatting"; \
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

# Install the executable globally using uv tool (force reinstall)
install-tool:
	uv tool install --force --reinstall .

# Uninstall the tool
uninstall-tool:
	uv tool uninstall scrawl2org