# Database Schema

## Tables

### `pdf_files`
Tracks PDF files and their metadata for change detection.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Auto-incrementing unique identifier |
| `filename` | TEXT NOT NULL UNIQUE | Full path to the PDF file |
| `file_hash` | TEXT NOT NULL | SHA-256 hash of the PDF file content |
| `last_processed` | TIMESTAMP | When this file was last processed |

### `page_images`
Stores extracted page images and their metadata.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Auto-incrementing unique identifier |
| `pdf_file_id` | INTEGER | Foreign key to `pdf_files.id` |
| `page_number` | INTEGER NOT NULL | Page number (0-based) |
| `image_data` | BLOB NOT NULL | PNG image data |
| `image_hash` | TEXT NOT NULL | SHA-256 hash of the image data |
| `last_updated` | TIMESTAMP | When this image was last updated |

### Indexes
- `idx_page_images_pdf_page` on `(pdf_file_id, page_number)` for fast page lookups
- `idx_page_images_hash` on `image_hash` for duplicate detection