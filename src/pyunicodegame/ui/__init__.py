"""
pyunicodegame.ui - UI components for TUI interfaces.

This module provides UI components including:
- BorderStyle: Box-drawing character configurations
- Panel: Windows/panels with borders and titles
- Text utilities for wrapping and alignment
"""

from .borders import BorderStyle
from .panel import Panel
from .text import wrap_text, align_text

__all__ = [
    "BorderStyle",
    "Panel",
    "wrap_text",
    "align_text",
]
