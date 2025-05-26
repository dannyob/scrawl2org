"""Main CLI entry point for scrawl2org."""

from pathlib import Path

import click

from .extractor import ImageExtractor
from .processor import PDFProcessor


@click.command()
@click.argument("pdf_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--database", "-d", default="scrawl2org.db", help="SQLite database file path"
)
@click.option(
    "--force", "-f", is_flag=True, help="Force processing even if PDF unchanged"
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option(
    "--extract",
    "-e",
    type=str,
    help='Extract pages instead of processing (format: page numbers or ranges, e.g., "1", "1-3", "1,3,5")',
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file for extracted image (default: stdout)",
)
@click.option(
    "--kitty",
    is_flag=True,
    help="Force Kitty image protocol display (even in non-Kitty terminals)",
)
@click.option(
    "--no-kitty", is_flag=True, help="Disable Kitty image protocol, output raw binary"
)
@click.option("--width", type=int, help="Display width in terminal cells (Kitty only)")
@click.option(
    "--height", type=int, help="Display height in terminal cells (Kitty only)"
)
def main(
    pdf_file: Path,
    database: str,
    force: bool,
    verbose: bool,
    extract: str,
    output: str,
    kitty: bool,
    no_kitty: bool,
    width: int,
    height: int,
):
    """Extract PDF pages as images and store in SQLite database.

    PDF_FILE: Path to the PDF file to process or extract from

    Examples:
        scrawl2org document.pdf                    # Process PDF and store images
        scrawl2org document.pdf -e 1               # Extract page 1 (Kitty terminal shows image)
        scrawl2org document.pdf -e 1 --kitty       # Force Kitty display in any terminal
        scrawl2org document.pdf -e 1 --width 40    # Display with specific width
        scrawl2org document.pdf -e 1 -o page.png  # Extract page 1 to file
        scrawl2org document.pdf -e 1-3 -o pages.png # Extract pages 1-3 to numbered files
    """
    try:
        if kitty and no_kitty:
            click.echo("Error: Cannot specify both --kitty and --no-kitty", err=True)
            raise click.Abort()

        if extract:
            # Extract mode - get images from database
            pdf_name = pdf_file.name
            extractor = ImageExtractor(database)

            # Configure display options
            display_options = {
                "force_kitty": kitty,
                "no_kitty": no_kitty,
                "width": width,
                "height": height,
            }
            extractor.extract_pages(pdf_name, extract, output, display_options)
        else:
            # Process mode - store PDF images in database
            processor = PDFProcessor(database)
            processor.process_pdf(str(pdf_file), force_update=force)

            if verbose:
                click.echo(f"Database: {database}")
                click.echo(f"PDF file: {pdf_file}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort() from e


if __name__ == "__main__":
    main()

