"""
pyunicodegame.themes - Visual theming system.

This module provides theming capabilities:
- Theme: Base theme configuration class
- CogmindTheme: Cogmind-inspired color palette
"""

from .theme import Theme
from .cogmind import CogmindTheme

__all__ = [
    "Theme",
    "CogmindTheme",
]
