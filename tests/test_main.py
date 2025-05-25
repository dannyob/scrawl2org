"""Tests for main CLI module."""

import pytest
import tempfile
import os
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from scrawl2org.main import main


@pytest.fixture
def sample_pdf():
    """Create a sample PDF file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        f.write(b'%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n')
        pdf_path = f.name
    
    yield pdf_path
    
    # Cleanup
    os.unlink(pdf_path)


def test_main_help():
    """Test CLI help output."""
    runner = CliRunner()
    result = runner.invoke(main, ['--help'])
    
    assert result.exit_code == 0
    assert 'Extract PDF pages as images' in result.output
    assert 'PDF_FILE' in result.output


def test_main_nonexistent_file():
    """Test CLI with non-existent PDF file."""
    runner = CliRunner()
    result = runner.invoke(main, ['/nonexistent/file.pdf'])
    
    assert result.exit_code != 0


@patch('scrawl2org.main.PDFProcessor')
def test_main_success(mock_processor_class, sample_pdf):
    """Test successful CLI execution."""
    mock_processor = MagicMock()
    mock_processor_class.return_value = mock_processor
    
    runner = CliRunner()
    result = runner.invoke(main, [sample_pdf])
    
    assert result.exit_code == 0
    mock_processor_class.assert_called_once_with('scrawl2org.db')
    mock_processor.process_pdf.assert_called_once_with(sample_pdf, force_update=False)


@patch('scrawl2org.main.PDFProcessor')
def test_main_with_options(mock_processor_class, sample_pdf):
    """Test CLI with various options."""
    mock_processor = MagicMock()
    mock_processor_class.return_value = mock_processor
    
    runner = CliRunner()
    result = runner.invoke(main, [
        sample_pdf,
        '--database', 'custom.db',
        '--force',
        '--verbose'
    ])
    
    assert result.exit_code == 0
    mock_processor_class.assert_called_once_with('custom.db')
    mock_processor.process_pdf.assert_called_once_with(sample_pdf, force_update=True)
    
    # Check verbose output
    assert 'Database: custom.db' in result.output
    assert f'PDF file: {sample_pdf}' in result.output


@patch('scrawl2org.main.PDFProcessor')
def test_main_processor_exception(mock_processor_class, sample_pdf):
    """Test CLI when processor raises an exception."""
    mock_processor = MagicMock()
    mock_processor.process_pdf.side_effect = Exception("Processing failed")
    mock_processor_class.return_value = mock_processor
    
    runner = CliRunner()
    result = runner.invoke(main, [sample_pdf])
    
    assert result.exit_code == 1
    assert 'Error: Processing failed' in result.output