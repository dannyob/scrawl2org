"""Main CLI entry point for scrawl2org."""

import click
from pathlib import Path
from .processor import PDFProcessor
from .extractor import ImageExtractor


@click.command()
@click.argument('pdf_file', type=click.Path(exists=True, path_type=Path))
@click.option('--database', '-d', default='scrawl2org.db', 
              help='SQLite database file path')
@click.option('--force', '-f', is_flag=True, 
              help='Force processing even if PDF unchanged')
@click.option('--verbose', '-v', is_flag=True, 
              help='Enable verbose output')
@click.option('--extract', '-e', type=str,
              help='Extract pages instead of processing (format: page numbers or ranges, e.g., "1", "1-3", "1,3,5")')
@click.option('--output', '-o', type=click.Path(),
              help='Output file for extracted image (default: stdout)')
def main(pdf_file: Path, database: str, force: bool, verbose: bool, extract: str, output: str):
    """Extract PDF pages as images and store in SQLite database.
    
    PDF_FILE: Path to the PDF file to process or extract from
    
    Examples:
        scrawl2org document.pdf                    # Process PDF and store images
        scrawl2org document.pdf -e 1               # Extract page 1 to stdout  
        scrawl2org document.pdf -e 1 -o page.png  # Extract page 1 to file
        scrawl2org document.pdf -e 1-3 -o pages.png # Extract pages 1-3 to numbered files
        scrawl2org document.pdf -e 1,3,5 -o pages.png # Extract specific pages to numbered files
    """
    try:
        if extract:
            # Extract mode - get images from database
            pdf_name = pdf_file.name
            extractor = ImageExtractor(database)
            extractor.extract_pages(pdf_name, extract, output)
        else:
            # Process mode - store PDF images in database
            processor = PDFProcessor(database)
            processor.process_pdf(str(pdf_file), force_update=force)
            
            if verbose:
                click.echo(f"Database: {database}")
                click.echo(f"PDF file: {pdf_file}")
                
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


if __name__ == '__main__':
    main()