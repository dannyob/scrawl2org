"""Kitty terminal image display support."""

import base64
import os
import sys
from typing import Optional


class KittyImageDisplay:
    """Display images using Kitty terminal's image protocol."""

    @staticmethod
    def is_kitty_terminal() -> bool:
        """Check if we're running in a Kitty terminal."""
        return (
            os.environ.get("TERM") == "xterm-kitty"
            or os.environ.get("KITTY_WINDOW_ID") is not None
        )

    @staticmethod
    def display_image(
        image_data: bytes,
        filename: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> None:
        """Display an image using Kitty's image protocol.

        Args:
            image_data: PNG image data
            filename: Optional filename for display (metadata only)
            width: Optional width in terminal cells
            height: Optional height in terminal cells
        """
        # Encode image data as base64
        encoded_data = base64.b64encode(image_data).decode("ascii")

        # Build the control sequence
        # Format: \x1b_G<key>=<value>,<key>=<value>...\x1b\
        params = []

        # Basic parameters
        params.append("a=T")  # action=transmit
        params.append("f=100")  # format=PNG

        # Optional display parameters
        if width:
            params.append(f"c={width}")  # columns
        if height:
            params.append(f"r={height}")  # rows

        # Optional filename for metadata (disabled for debugging)
        # if filename:
        #     filename_b64 = base64.b64encode(filename.encode('utf-8')).decode('ascii')
        #     params.append(f"N={filename_b64}")

        # Construct the full escape sequence
        param_string = ",".join(params)

        # Split data into chunks (Kitty has a limit on payload size)
        chunk_size = 4096
        chunks = [
            encoded_data[i : i + chunk_size]
            for i in range(0, len(encoded_data), chunk_size)
        ]

        for i, chunk in enumerate(chunks):
            if len(chunks) == 1:
                # Single chunk - no need for m parameter
                escape_seq = f"\x1b_G{param_string};{chunk}\x1b\\"
            elif i == 0:
                # First of multiple chunks
                escape_seq = f"\x1b_G{param_string},m=1;{chunk}\x1b\\"
            elif i == len(chunks) - 1:
                # Last chunk
                escape_seq = f"\x1b_Gm=0;{chunk}\x1b\\"
            else:
                # Middle chunk
                escape_seq = f"\x1b_Gm=1;{chunk}\x1b\\"

            sys.stdout.write(escape_seq)
            sys.stdout.flush()

        # Add a newline after the image
        print()

    @staticmethod
    def display_image_inline(image_data: bytes, filename: Optional[str] = None) -> None:
        """Display an image inline (letting Kitty auto-size it).

        Args:
            image_data: PNG image data
            filename: Optional filename for display
        """
        KittyImageDisplay.display_image(image_data, filename)

    @staticmethod
    def display_image_sized(
        image_data: bytes, width: int, height: int, filename: Optional[str] = None
    ) -> None:
        """Display an image with specific terminal cell dimensions.

        Args:
            image_data: PNG image data
            width: Width in terminal cells
            height: Height in terminal cells
            filename: Optional filename for display
        """
        KittyImageDisplay.display_image(image_data, filename, width, height)

