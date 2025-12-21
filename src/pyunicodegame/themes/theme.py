"""
pyunicodegame.themes.theme - Theme configuration class.

QUICK START:
    from pyunicodegame.themes import Theme

    # Create custom theme
    my_theme = Theme(
        background=(10, 10, 20),
        foreground=(200, 200, 200),
        accent=(0, 255, 128),
    )

    renderer = Renderer(width=80, height=25, theme=my_theme)

CLASSES:
    Theme: Complete visual theme configuration

Themes provide a centralized way to configure colors and visual style
across the entire application.
"""

from dataclasses import dataclass, field
from typing import List, Optional

from ..core.colors import Color


@dataclass
class Theme:
    """
    Complete visual theme configuration.

    Themes define colors for all visual elements including
    backgrounds, foregrounds, UI components, and effects.

    Attributes:
        name: Theme identifier
        background: Default background color
        foreground: Default text color
        accent: Primary accent color
        panel_bg: Panel/window background
        panel_border: Panel border color
        panel_title: Panel title text color
        player_color: Player entity color
        enemy_color: Enemy entity color
        item_color: Item/pickup color
        positive: Positive feedback color (health, success)
        negative: Negative feedback color (damage, error)
        warning: Warning color
        info: Informational text color
        glow_default: Default glow effect color
        palette: Additional colors for variety
    """
    name: str = "default"

    # Base colors
    background: Color = (10, 10, 15)
    foreground: Color = (200, 200, 200)
    accent: Color = (100, 200, 255)

    # UI colors
    panel_bg: Color = (20, 20, 30)
    panel_border: Color = (60, 60, 80)
    panel_title: Color = (255, 255, 100)

    # Entity colors
    player_color: Color = (0, 255, 0)
    enemy_color: Color = (255, 50, 50)
    ally_color: Color = (100, 200, 255)
    neutral_color: Color = (200, 200, 100)
    item_color: Color = (255, 200, 50)

    # Semantic colors
    positive: Color = (0, 255, 0)
    negative: Color = (255, 0, 0)
    warning: Color = (255, 200, 0)
    info: Color = (100, 150, 255)
    muted: Color = (100, 100, 100)

    # Effect colors
    glow_default: Color = (100, 150, 255)
    damage_flash: Color = (255, 50, 50)
    heal_flash: Color = (0, 255, 100)
    magic_color: Color = (200, 100, 255)

    # Palette for random selection or variety
    palette: List[Color] = field(default_factory=lambda: [
        (255, 100, 100),  # Red
        (100, 255, 100),  # Green
        (100, 100, 255),  # Blue
        (255, 255, 100),  # Yellow
        (255, 100, 255),  # Magenta
        (100, 255, 255),  # Cyan
        (255, 200, 100),  # Orange
    ])

    def get_health_color(self, percent: float) -> Color:
        """
        Get a color based on health percentage.

        Args:
            percent: Health percentage (0.0 to 1.0)

        Returns:
            Color ranging from negative (low) to positive (high)
        """
        if percent > 0.66:
            return self.positive
        elif percent > 0.33:
            return self.warning
        else:
            return self.negative

    def get_stat_color(self, value: float, max_value: float) -> Color:
        """
        Get a color based on a stat value.

        Args:
            value: Current value
            max_value: Maximum value

        Returns:
            Appropriate color based on percentage
        """
        if max_value <= 0:
            return self.muted
        return self.get_health_color(value / max_value)

    def lerp_palette(self, t: float) -> Color:
        """
        Interpolate through the palette.

        Args:
            t: Position in palette (0.0 to 1.0)

        Returns:
            Interpolated color from palette
        """
        if not self.palette:
            return self.foreground

        t = max(0.0, min(1.0, t))
        idx = t * (len(self.palette) - 1)
        lower = int(idx)
        upper = min(lower + 1, len(self.palette) - 1)
        frac = idx - lower

        c1 = self.palette[lower]
        c2 = self.palette[upper]

        return (
            int(c1[0] + (c2[0] - c1[0]) * frac),
            int(c1[1] + (c2[1] - c1[1]) * frac),
            int(c1[2] + (c2[2] - c1[2]) * frac),
        )

    def with_overrides(self, **kwargs) -> "Theme":
        """
        Create a new theme with some values overridden.

        Args:
            **kwargs: Theme attributes to override

        Returns:
            New Theme instance with overrides applied
        """
        import dataclasses
        return dataclasses.replace(self, **kwargs)


# Preset themes

DARK_THEME = Theme(
    name="dark",
    background=(5, 5, 10),
    foreground=(180, 180, 180),
    accent=(80, 160, 255),
    panel_bg=(15, 15, 25),
    panel_border=(40, 40, 60),
    panel_title=(200, 200, 255),
)

LIGHT_THEME = Theme(
    name="light",
    background=(240, 240, 235),
    foreground=(30, 30, 30),
    accent=(0, 100, 200),
    panel_bg=(255, 255, 255),
    panel_border=(180, 180, 180),
    panel_title=(0, 0, 0),
    positive=(0, 150, 0),
    negative=(200, 0, 0),
    warning=(180, 140, 0),
)

RETRO_GREEN_THEME = Theme(
    name="retro_green",
    background=(0, 10, 0),
    foreground=(0, 255, 0),
    accent=(100, 255, 100),
    panel_bg=(0, 20, 0),
    panel_border=(0, 100, 0),
    panel_title=(150, 255, 150),
    player_color=(0, 255, 0),
    enemy_color=(255, 100, 100),
    positive=(100, 255, 100),
    negative=(255, 100, 100),
    warning=(255, 255, 0),
    glow_default=(0, 200, 0),
)

AMBER_THEME = Theme(
    name="amber",
    background=(10, 5, 0),
    foreground=(255, 180, 0),
    accent=(255, 220, 100),
    panel_bg=(20, 10, 0),
    panel_border=(150, 100, 0),
    panel_title=(255, 220, 100),
    player_color=(255, 200, 0),
    glow_default=(255, 180, 50),
)
