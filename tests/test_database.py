"""Tests for database module."""

import os
import tempfile

import pytest

from scrawl2org.database import Database


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    db = Database(db_path)
    yield db

    # Cleanup
    os.unlink(db_path)


@pytest.fixture
def sample_pdf():
    """Create a sample PDF file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        # Write some dummy PDF content
        f.write(b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
        pdf_path = f.name

    yield pdf_path

    # Cleanup
    os.unlink(pdf_path)


def test_database_initialization(temp_db):
    """Test that database tables are created properly."""
    # Database should be initialized without errors
    assert os.path.exists(temp_db.db_path)


def test_file_hash_calculation(temp_db, sample_pdf):
    """Test file hash calculation."""
    hash1 = temp_db.get_file_hash(sample_pdf)
    hash2 = temp_db.get_file_hash(sample_pdf)

    # Hash should be consistent
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 hex length


def test_image_hash_calculation(temp_db):
    """Test image hash calculation."""
    image_data = b"fake image data"
    hash1 = temp_db.get_image_hash(image_data)
    hash2 = temp_db.get_image_hash(image_data)

    # Hash should be consistent
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 hex length


def test_pdf_change_detection_new_file(temp_db, sample_pdf):
    """Test change detection for new PDF file."""
    has_changed, pdf_file_id = temp_db.check_pdf_changed(sample_pdf)

    assert has_changed is True
    assert pdf_file_id is None


def test_pdf_change_detection_unchanged_file(temp_db, sample_pdf):
    """Test change detection for unchanged PDF file."""
    # First time - should be new
    has_changed, pdf_file_id = temp_db.check_pdf_changed(sample_pdf)
    assert has_changed is True
    assert pdf_file_id is None

    # Register the file
    pdf_file_id = temp_db.update_pdf_file(sample_pdf)

    # Second time - should be unchanged
    has_changed, returned_id = temp_db.check_pdf_changed(sample_pdf)
    assert has_changed is False
    assert returned_id == pdf_file_id


def test_pdf_file_update(temp_db, sample_pdf):
    """Test PDF file record update."""
    # Insert new file
    pdf_file_id = temp_db.update_pdf_file(sample_pdf)
    assert pdf_file_id is not None

    # Update existing file
    same_id = temp_db.update_pdf_file(sample_pdf, pdf_file_id)
    assert same_id == pdf_file_id


def test_page_image_storage(temp_db, sample_pdf):
    """Test storing and retrieving page images."""
    pdf_file_id = temp_db.update_pdf_file(sample_pdf)
    image_data = b"fake png image data"

    # Store image
    temp_db.store_page_image(pdf_file_id, 0, image_data)

    # Check if image exists
    existing_hash = temp_db.get_existing_page_image(pdf_file_id, 0)
    expected_hash = temp_db.get_image_hash(image_data)
    assert existing_hash == expected_hash

    # Non-existent page should return None
    assert temp_db.get_existing_page_image(pdf_file_id, 99) is None


def test_page_image_update(temp_db, sample_pdf):
    """Test updating existing page images."""
    pdf_file_id = temp_db.update_pdf_file(sample_pdf)

    # Store initial image
    image_data1 = b"original image data"
    temp_db.store_page_image(pdf_file_id, 0, image_data1)
    hash1 = temp_db.get_existing_page_image(pdf_file_id, 0)

    # Update with new image
    image_data2 = b"updated image data"
    temp_db.store_page_image(pdf_file_id, 0, image_data2)
    hash2 = temp_db.get_existing_page_image(pdf_file_id, 0)

    # Hashes should be different
    assert hash1 != hash2
    assert hash2 == temp_db.get_image_hash(image_data2)


def test_delete_old_pages(temp_db, sample_pdf):
    """Test deletion of old pages when PDF page count decreases."""
    pdf_file_id = temp_db.update_pdf_file(sample_pdf)

    # Store images for 3 pages
    for page_num in range(3):
        image_data = f"page {page_num} data".encode()
        temp_db.store_page_image(pdf_file_id, page_num, image_data)

    # Verify all pages exist
    for page_num in range(3):
        assert temp_db.get_existing_page_image(pdf_file_id, page_num) is not None

    # Delete pages 2 and above (keep only 2 pages)
    temp_db.delete_old_pages(pdf_file_id, 2)

    # Check results
    assert temp_db.get_existing_page_image(pdf_file_id, 0) is not None
    assert temp_db.get_existing_page_image(pdf_file_id, 1) is not None
    assert temp_db.get_existing_page_image(pdf_file_id, 2) is None


def test_page_image_storage_with_ocr(temp_db, sample_pdf):
    """Test storing page images with OCR text."""
    pdf_file_id = temp_db.update_pdf_file(sample_pdf)
    image_data = b"fake png image data"
    ocr_result = {"text": "Sample OCR text", "confidence": 0.95, "engine": "test"}

    # Store image with OCR
    temp_db.store_page_image(pdf_file_id, 0, image_data, ocr_result)

    # Retrieve OCR text
    retrieved_ocr = temp_db.get_page_ocr_text(pdf_file_id, 0)
    assert retrieved_ocr == ocr_result

    # Non-existent page should return None
    assert temp_db.get_page_ocr_text(pdf_file_id, 99) is None


def test_update_page_ocr_text(temp_db, sample_pdf):
    """Test updating OCR text for existing pages."""
    pdf_file_id = temp_db.update_pdf_file(sample_pdf)
    image_data = b"fake png image data"

    # Store image without OCR
    temp_db.store_page_image(pdf_file_id, 0, image_data)

    # Should have no OCR text initially
    assert temp_db.get_page_ocr_text(pdf_file_id, 0) is None

    # Update with OCR text
    ocr_result = {"text": "Updated OCR text", "confidence": 0.88, "engine": "updated"}
    temp_db.update_page_ocr_text(pdf_file_id, 0, ocr_result)

    # Retrieve updated OCR text
    retrieved_ocr = temp_db.get_page_ocr_text(pdf_file_id, 0)
    assert retrieved_ocr == ocr_result
