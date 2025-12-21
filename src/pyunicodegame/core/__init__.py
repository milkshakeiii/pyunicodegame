"""
pyunicodegame.core - Core rendering components.

This module provides the foundational classes for grid-based unicode rendering:
- Cell: A single cell in the grid with character, colors, and glow
- Grid: A 2D buffer of cells with dirty tracking
- GlyphCache: Efficient caching of rendered character sprites
- Renderer: The main interface for all rendering operations
"""

from .colors import Color, lerp_color, brighten, darken
from .grid import Cell, Grid
from .glyph_cache import GlyphCache
from .renderer import Renderer

__all__ = [
    "Color",
    "lerp_color",
    "brighten",
    "darken",
    "Cell",
    "Grid",
    "GlyphCache",
    "Renderer",
]
