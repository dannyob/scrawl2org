"""Main CLI entry point for scrawl2org."""

import click
from pathlib import Path
from .processor import PDFProcessor


@click.command()
@click.argument('pdf_file', type=click.Path(exists=True, path_type=Path))
@click.option('--database', '-d', default='scrawl2org.db', 
              help='SQLite database file path')
@click.option('--force', '-f', is_flag=True, 
              help='Force processing even if PDF unchanged')
@click.option('--verbose', '-v', is_flag=True, 
              help='Enable verbose output')
def main(pdf_file: Path, database: str, force: bool, verbose: bool):
    """Extract PDF pages as images and store in SQLite database.
    
    PDF_FILE: Path to the PDF file to process
    """
    try:
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