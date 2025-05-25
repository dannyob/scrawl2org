"""Database operations for PDF image storage."""

import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple


class Database:
    """Manages SQLite database for PDF image storage."""
    
    def __init__(self, db_path: str = "scrawl2org.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
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
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT id, file_hash FROM pdf_files WHERE filename = ?",
                (filename,)
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
        now = datetime.now()
        
        with sqlite3.connect(self.db_path) as conn:
            if pdf_file_id is None:
                cursor = conn.execute(
                    "INSERT INTO pdf_files (filename, file_hash, last_processed) VALUES (?, ?, ?)",
                    (filename, current_hash, now)
                )
                return cursor.lastrowid
            else:
                conn.execute(
                    "UPDATE pdf_files SET file_hash = ?, last_processed = ? WHERE id = ?",
                    (current_hash, now, pdf_file_id)
                )
                return pdf_file_id
    
    def get_existing_page_image(self, pdf_file_id: int, page_number: int) -> Optional[str]:
        """Get hash of existing page image if it exists."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT image_hash FROM page_images WHERE pdf_file_id = ? AND page_number = ?",
                (pdf_file_id, page_number)
            )
            row = cursor.fetchone()
            return row[0] if row else None
    
    def store_page_image(self, pdf_file_id: int, page_number: int, image_data: bytes):
        """Store or update a page image."""
        image_hash = self.get_image_hash(image_data)
        now = datetime.now()
        
        with sqlite3.connect(self.db_path) as conn:
            existing_hash = self.get_existing_page_image(pdf_file_id, page_number)
            
            if existing_hash is None:
                conn.execute(
                    """INSERT INTO page_images 
                       (pdf_file_id, page_number, image_data, image_hash, last_updated)
                       VALUES (?, ?, ?, ?, ?)""",
                    (pdf_file_id, page_number, image_data, image_hash, now)
                )
            elif existing_hash != image_hash:
                conn.execute(
                    """UPDATE page_images 
                       SET image_data = ?, image_hash = ?, last_updated = ?
                       WHERE pdf_file_id = ? AND page_number = ?""",
                    (image_data, image_hash, now, pdf_file_id, page_number)
                )
            
            conn.commit()
    
    def delete_old_pages(self, pdf_file_id: int, current_page_count: int):
        """Delete page images that no longer exist in the PDF."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "DELETE FROM page_images WHERE pdf_file_id = ? AND page_number >= ?",
                (pdf_file_id, current_page_count)
            )
            conn.commit()