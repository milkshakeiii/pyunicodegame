"""
pyunicodegame.themes.cogmind - Cogmind-inspired visual theme.

QUICK START:
    from pyunicodegame.themes import CogmindTheme

    renderer = Renderer(width=80, height=25, theme=CogmindTheme())

CLASSES:
    CogmindTheme: A theme inspired by Cogmind's color palette

The Cogmind theme uses a dark, sci-fi aesthetic with cyan/blue accents
and careful use of color to convey information.
"""

from dataclasses import dataclass, field
from typing import List

from ..core.colors import Color
from .theme import Theme


@dataclass
class CogmindTheme(Theme):
    """
    A theme inspired by Cogmind's visual style.

    Cogmind uses a dark background with carefully chosen colors
    to convey information at a glance. This theme captures that
    aesthetic while being suitable for general TUI games.

    Key characteristics:
    - Very dark background with subtle blue tint
    - Cyan/blue accent colors
    - Warm colors (yellow, orange) for important items
    - Red for damage/enemies
    - Green for the player and positive effects
    """
    name: str = "cogmind"

    # Base colors - very dark with blue tint
    background: Color = (5, 8, 12)
    foreground: Color = (160, 170, 180)
    accent: Color = (80, 180, 220)

    # UI colors - subtle, not distracting
    panel_bg: Color = (12, 16, 22)
    panel_border: Color = (40, 60, 80)
    panel_title: Color = (100, 180, 220)

    # Entity colors
    player_color: Color = (50, 220, 80)
    enemy_color: Color = (220, 60, 60)
    ally_color: Color = (80, 160, 220)
    neutral_color: Color = (180, 180, 120)
    item_color: Color = (220, 180, 60)

    # Semantic colors
    positive: Color = (60, 220, 100)
    negative: Color = (220, 50, 50)
    warning: Color = (220, 180, 40)
    info: Color = (80, 160, 220)
    muted: Color = (80, 90, 100)

    # Effect colors
    glow_default: Color = (80, 160, 220)
    damage_flash: Color = (255, 80, 80)
    heal_flash: Color = (80, 255, 120)
    magic_color: Color = (180, 100, 220)

    # Extended palette for variety
    palette: List[Color] = field(default_factory=lambda: [
        (220, 60, 60),    # Alert red
        (220, 140, 40),   # Warning orange
        (220, 200, 60),   # Caution yellow
        (60, 220, 100),   # Safe green
        (80, 180, 220),   # Info cyan
        (100, 120, 220),  # Calm blue
        (180, 100, 220),  # Exotic purple
        (160, 170, 180),  # Neutral gray
    ])

    # Cogmind-specific colors for common elements
    power_color: Color = (220, 180, 40)     # Power/energy
    heat_color: Color = (220, 100, 40)      # Heat/thermal
    matter_color: Color = (120, 180, 80)    # Matter/physical
    data_color: Color = (80, 160, 220)      # Data/information

    def get_integrity_color(self, percent: float) -> Color:
        """
        Get color for integrity/durability display.

        Uses Cogmind-style color coding:
        - 100-67%: Green (good)
        - 66-34%: Yellow (caution)
        - 33-1%: Red (critical)
        """
        if percent > 0.66:
            return (60, 180, 80)  # Healthy green
        elif percent > 0.33:
            return (200, 180, 40)  # Caution yellow
        else:
            return (200, 60, 60)  # Critical red

    def get_heat_color(self, percent: float) -> Color:
        """
        Get color for heat/temperature display.

        Ranges from cool blue through yellow to hot red.
        """
        if percent < 0.33:
            # Cool - blue to cyan
            t = percent / 0.33
            return (
                int(40 + 40 * t),
                int(80 + 100 * t),
                int(180 - 60 * t),
            )
        elif percent < 0.66:
            # Warm - cyan to yellow
            t = (percent - 0.33) / 0.33
            return (
                int(80 + 140 * t),
                int(180),
                int(120 - 80 * t),
            )
        else:
            # Hot - yellow to red
            t = (percent - 0.66) / 0.34
            return (
                220,
                int(180 - 120 * t),
                int(40),
            )


# Variations of the Cogmind theme

class CogmindBrightTheme(CogmindTheme):
    """
    A brighter variant of the Cogmind theme.

    Useful for better visibility or personal preference.
    """
    name: str = "cogmind_bright"
    background: Color = (15, 20, 28)
    foreground: Color = (200, 210, 220)
    panel_bg: Color = (25, 32, 42)
    panel_border: Color = (60, 85, 110)


class CogmindWarmTheme(CogmindTheme):
    """
    A warmer variant with orange/amber accents.
    """
    name: str = "cogmind_warm"
    accent: Color = (220, 160, 60)
    panel_title: Color = (220, 180, 80)
    glow_default: Color = (220, 160, 80)
    info: Color = (200, 160, 80)


class CogmindMinimalTheme(CogmindTheme):
    """
    A more minimal variant with reduced color usage.

    Uses mostly grayscale with color only for important elements.
    """
    name: str = "cogmind_minimal"
    foreground: Color = (140, 140, 140)
    panel_border: Color = (50, 50, 55)
    muted: Color = (70, 70, 75)

    # Keep accent colors vivid for contrast
    accent: Color = (80, 200, 240)
    player_color: Color = (80, 240, 120)
    enemy_color: Color = (240, 80, 80)
