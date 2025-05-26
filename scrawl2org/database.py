"""Database operations for PDF image storage."""

import hashlib
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class Database:
    """Manages SQLite database for PDF image storage."""

    def __init__(self, db_path: str = "scrawl2org.db"):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize database tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            # Check if we need to migrate existing tables
            self._migrate_database(conn)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS pdf_files (
                    id INTEGER PRIMARY KEY,
                    filename TEXT NOT NULL UNIQUE,
                    file_hash TEXT NOT NULL,
                    last_processed TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS page_images (
                    id INTEGER PRIMARY KEY,
                    pdf_file_id INTEGER,
                    page_number INTEGER NOT NULL,
                    image_data BLOB NOT NULL,
                    image_hash TEXT NOT NULL,
                    last_updated TIMESTAMP,
                    ocr_text JSON,
                    FOREIGN KEY (pdf_file_id) REFERENCES pdf_files (id)
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_page_images_pdf_page
                ON page_images (pdf_file_id, page_number)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_page_images_hash
                ON page_images (image_hash)
            """)

            conn.commit()

    def _migrate_database(self, conn):
        """Handle database migrations for existing databases."""
        # Check if page_images table exists first
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='page_images'"
        )
        if cursor.fetchone():
            # Table exists, check if ocr_text column exists
            cursor = conn.execute("PRAGMA table_info(page_images)")
            columns = [row[1] for row in cursor.fetchall()]

            if "ocr_text" not in columns:
                # Add ocr_text column to existing table
                conn.execute("ALTER TABLE page_images ADD COLUMN ocr_text JSON")
                conn.commit()

    def get_file_hash(self, filename: str) -> str:
        """Calculate SHA-256 hash of a file."""
        sha256_hash = hashlib.sha256()
        with open(filename, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    def get_image_hash(self, image_data: bytes) -> str:
        """Calculate SHA-256 hash of image data."""
        return hashlib.sha256(image_data).hexdigest()

    def check_pdf_changed(self, filename: str) -> Tuple[bool, Optional[int]]:
        """Check if PDF file has changed since last processing.

        Returns:
            Tuple of (has_changed, pdf_file_id)
            has_changed is True if file is new or content changed
            pdf_file_id is None if file is new
        """
        current_hash = self.get_file_hash(filename)
        basename = Path(filename).name

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT id, file_hash FROM pdf_files WHERE filename = ?", (basename,)
            )
            row = cursor.fetchone()

            if row is None:
                return True, None

            pdf_file_id, stored_hash = row
            return current_hash != stored_hash, pdf_file_id

    def update_pdf_file(self, filename: str, pdf_file_id: Optional[int] = None) -> int:
        """Update or insert PDF file record.

        Returns:
            The pdf_file_id of the updated/inserted record
        """
        current_hash = self.get_file_hash(filename)
        basename = Path(filename).name
        now = datetime.now()

        with sqlite3.connect(self.db_path) as conn:
            if pdf_file_id is None:
                cursor = conn.execute(
                    "INSERT INTO pdf_files (filename, file_hash, last_processed) VALUES (?, ?, ?)",
                    (basename, current_hash, now),
                )
                return cursor.lastrowid
            else:
                conn.execute(
                    "UPDATE pdf_files SET filename = ?, file_hash = ?, last_processed = ? WHERE id = ?",
                    (basename, current_hash, now, pdf_file_id),
                )
                return pdf_file_id

    def get_existing_page_image(
        self, pdf_file_id: int, page_number: int
    ) -> Optional[str]:
        """Get hash of existing page image if it exists."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT image_hash FROM page_images WHERE pdf_file_id = ? AND page_number = ?",
                (pdf_file_id, page_number),
            )
            row = cursor.fetchone()
            return row[0] if row else None

    def store_page_image(
        self,
        pdf_file_id: int,
        page_number: int,
        image_data: bytes,
        ocr_text: Optional[Dict[str, Any]] = None,
    ):
        """Store or update a page image with optional OCR text.

        Args:
            pdf_file_id: PDF file ID
            page_number: Page number
            image_data: PNG image data as bytes
            ocr_text: OCR results as dictionary (will be stored as JSON)
        """
        image_hash = self.get_image_hash(image_data)
        now = datetime.now()
        ocr_json = json.dumps(ocr_text) if ocr_text else None

        with sqlite3.connect(self.db_path) as conn:
            existing_hash = self.get_existing_page_image(pdf_file_id, page_number)

            if existing_hash is None:
                conn.execute(
                    """INSERT INTO page_images
                       (pdf_file_id, page_number, image_data, image_hash, last_updated, ocr_text)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (pdf_file_id, page_number, image_data, image_hash, now, ocr_json),
                )
            elif existing_hash != image_hash:
                conn.execute(
                    """UPDATE page_images
                       SET image_data = ?, image_hash = ?, last_updated = ?, ocr_text = ?
                       WHERE pdf_file_id = ? AND page_number = ?""",
                    (image_data, image_hash, now, ocr_json, pdf_file_id, page_number),
                )

            conn.commit()

    def delete_old_pages(self, pdf_file_id: int, current_page_count: int):
        """Delete page images that no longer exist in the PDF."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "DELETE FROM page_images WHERE pdf_file_id = ? AND page_number >= ?",
                (pdf_file_id, current_page_count),
            )
            conn.commit()

    def get_pdf_file_id(self, filename: str) -> Optional[int]:
        """Get PDF file ID by filename.

        Args:
            filename: Name of the PDF file (basename only)

        Returns:
            PDF file ID if found, None otherwise
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT id FROM pdf_files WHERE filename = ?", (filename,)
            )
            row = cursor.fetchone()
            return row[0] if row else None

    def get_page_image(self, pdf_file_id: int, page_number: int) -> Optional[bytes]:
        """Get page image data by PDF file ID and page number.

        Args:
            pdf_file_id: PDF file ID
            page_number: Page number (0-based)

        Returns:
            Image data as bytes if found, None otherwise
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT image_data FROM page_images WHERE pdf_file_id = ? AND page_number = ?",
                (pdf_file_id, page_number),
            )
            row = cursor.fetchone()
            return row[0] if row else None

    def list_pdf_files(self) -> List[str]:
        """List all PDF files in the database.

        Returns:
            List of PDF filenames
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT filename FROM pdf_files ORDER BY filename")
            return [row[0] for row in cursor.fetchall()]

    def get_page_count(self, pdf_file_id: int) -> int:
        """Get the number of pages stored for a PDF file.

        Args:
            pdf_file_id: PDF file ID

        Returns:
            Number of pages stored
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM page_images WHERE pdf_file_id = ?", (pdf_file_id,)
            )
            return cursor.fetchone()[0]

    def get_page_ocr_text(
        self, pdf_file_id: int, page_number: int
    ) -> Optional[Dict[str, Any]]:
        """Get OCR text for a specific page.

        Args:
            pdf_file_id: PDF file ID
            page_number: Page number (0-based)

        Returns:
            OCR text data as dictionary if found, None otherwise
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT ocr_text FROM page_images WHERE pdf_file_id = ? AND page_number = ?",
                (pdf_file_id, page_number),
            )
            row = cursor.fetchone()
            if row and row[0]:
                return json.loads(row[0])
            return None

    def update_page_ocr_text(
        self, pdf_file_id: int, page_number: int, ocr_text: Dict[str, Any]
    ):
        """Update OCR text for an existing page.

        Args:
            pdf_file_id: PDF file ID
            page_number: Page number (0-based)
            ocr_text: OCR results as dictionary
        """
        ocr_json = json.dumps(ocr_text)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE page_images SET ocr_text = ? WHERE pdf_file_id = ? AND page_number = ?",
                (ocr_json, pdf_file_id, page_number),
            )
            conn.commit()
