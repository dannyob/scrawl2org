"""Image extraction from database."""

import sys
import re
from typing import List, Set
from .database import Database


class ImageExtractor:
    """Extracts page images from database."""
    
    def __init__(self, db_path: str = "scrawl2org.db"):
        self.db = Database(db_path)
    
    def parse_page_range(self, pages_str: str) -> Set[int]:
        """Parse page range string into set of page numbers.
        
        Examples:
            "1" -> {1}
            "1-3" -> {1, 2, 3}
            "1,3,5" -> {1, 3, 5}
            "1-3,5,7-9" -> {1, 2, 3, 5, 7, 8, 9}
        
        Args:
            pages_str: Page specification string
            
        Returns:
            Set of page numbers (1-based)
            
        Raises:
            ValueError: If page specification is invalid
        """
        page_numbers = set()
        
        # Split by commas
        parts = [part.strip() for part in pages_str.split(',')]
        
        for part in parts:
            if not part:
                continue
                
            # Check if it's a range (e.g., "1-3")
            range_match = re.match(r'^(\d+)\s*-\s*(\d+)$', part)
            if range_match:
                start, end = int(range_match.group(1)), int(range_match.group(2))
                if start > end:
                    raise ValueError(f"Invalid range: start ({start}) > end ({end})")
                if start < 1:
                    raise ValueError(f"Page numbers must be >= 1, got: {start}")
                
                page_numbers.update(range(start, end + 1))
            else:
                # Single page number (including negative numbers)
                page_match = re.match(r'^(-?\d+)$', part)
                if not page_match:
                    raise ValueError(f"Invalid page number: {part}")
                
                page_num = int(page_match.group(1))
                if page_num < 1:
                    raise ValueError(f"Page numbers must be >= 1, got: {page_num}")
                
                page_numbers.add(page_num)
        
        if not page_numbers:
            raise ValueError("No valid page numbers specified")
        
        return page_numbers
    
    def extract_pages(self, pdf_name: str, pages_str: str, output_path: str = None, format: str = 'png'):
        """Extract page images from database.
        
        Args:
            pdf_name: Name of PDF file (filename only, not full path)
            pages_str: Page specification string
            output_path: Output file path, or None for stdout
            format: Output format (currently only 'png')
        """
        # Parse page numbers
        page_numbers = self.parse_page_range(pages_str)
        
        # Get PDF file ID
        pdf_file_id = self.db.get_pdf_file_id(pdf_name)
        if pdf_file_id is None:
            raise ValueError(f"PDF file not found in database: {pdf_name}")
        
        # Handle single page vs multiple pages
        if len(page_numbers) == 1:
            page_num = list(page_numbers)[0]
            image_data = self.db.get_page_image(pdf_file_id, page_num - 1)  # Convert to 0-based
            
            if image_data is None:
                raise ValueError(f"Page {page_num} not found for PDF: {pdf_name}")
            
            self._output_image(image_data, output_path, page_num)
        else:
            # Multiple pages
            if output_path is None:
                raise ValueError("Multiple pages cannot be output to stdout (PNG files cannot be concatenated). Please specify an output file pattern with -o.")
            
            # Extract base name and extension for numbering
            from pathlib import Path
            output_path_obj = Path(output_path)
            base_name = output_path_obj.stem
            extension = output_path_obj.suffix or '.png'
            parent_dir = output_path_obj.parent
            
            for page_num in sorted(page_numbers):
                image_data = self.db.get_page_image(pdf_file_id, page_num - 1)  # Convert to 0-based
                
                if image_data is None:
                    print(f"Warning: Page {page_num} not found for PDF: {pdf_name}", file=sys.stderr)
                    continue
                
                # Create numbered filename
                numbered_filename = parent_dir / f"{base_name}_page{page_num:03d}{extension}"
                self._output_image(image_data, str(numbered_filename), page_num)
    
    def _output_image(self, image_data: bytes, output_path: str = None, page_num: int = None):
        """Output image data to file or stdout.
        
        Args:
            image_data: PNG image data
            output_path: Output file path, or None for stdout
            page_num: Page number for logging (optional)
        """
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(image_data)
            if page_num:
                print(f"Page {page_num} written to: {output_path}", file=sys.stderr)
            else:
                print(f"Image written to: {output_path}", file=sys.stderr)
        else:
            # Output to stdout
            sys.stdout.buffer.write(image_data)