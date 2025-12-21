"""
pyunicodegame.core.fonts - Font loading utilities.

QUICK START:
    from pyunicodegame.core.fonts import get_default_font_path, load_font

    font = load_font()  # Uses bundled 10x20.bdf
    font = load_font("/path/to/custom.bdf")

FUNCTIONS:
    get_default_font_path() - Get path to the bundled 10x20.bdf font
    load_font(path) - Load a BDF font via pygame.freetype
    get_font_dimensions(font) - Get tile width/height from a font
"""

import os
from typing import Optional, Tuple

import pygame
import pygame.freetype


def get_default_font_path() -> str:
    """
    Get the path to the bundled default font (10x20.bdf).

    Returns:
        Absolute path to the bundled BDF font file.
    """
    return os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "bundled_fonts",
        "10x20.bdf"
    )


def load_font(font_path: Optional[str] = None) -> pygame.freetype.Font:
    """
    Load a BDF font for rendering.

    Args:
        font_path: Path to a BDF font file. If None, uses the bundled default.

    Returns:
        A pygame.freetype.Font object.

    Raises:
        FileNotFoundError: If the font file doesn't exist.
        pygame.error: If the font cannot be loaded.
    """
    if font_path is None:
        font_path = get_default_font_path()

    if not os.path.exists(font_path):
        raise FileNotFoundError(f"Font file not found: {font_path}")

    pygame.freetype.init()
    return pygame.freetype.Font(font_path)


def get_font_dimensions(font: pygame.freetype.Font) -> Tuple[int, int]:
    """
    Get the tile dimensions for a font by rendering a test character.

    BDF fonts have fixed dimensions, so we render a full-block character
    to measure the cell size.

    Args:
        font: A loaded pygame.freetype.Font object.

    Returns:
        Tuple of (width, height) in pixels.
    """
    # Render a full block character to get dimensions
    surf, _ = font.render("\u2588", (255, 255, 255))  # Unicode full block
    return surf.get_width(), surf.get_height()
