"""
pyunicodegame.core.colors - Color type and utilities.

QUICK START:
    from pyunicodegame.core import Color, lerp_color, brighten

    red: Color = (255, 0, 0)
    orange = lerp_color(red, (255, 255, 0), 0.5)
    bright_red = brighten(red, 0.3)

TYPES:
    Color: Tuple[int, int, int] - RGB color with values 0-255

FUNCTIONS:
    lerp_color(a, b, t) - Linear interpolation between two colors
    brighten(color, amount) - Brighten a color by a factor
    darken(color, amount) - Darken a color by a factor
    clamp_color(color) - Ensure color values are in valid range
"""

from typing import Tuple

# Type alias for RGB colors
Color = Tuple[int, int, int]


def clamp(value: int, min_val: int = 0, max_val: int = 255) -> int:
    """Clamp a value to a range."""
    return max(min_val, min(max_val, value))


def clamp_color(color: Color) -> Color:
    """Ensure all color components are in the valid 0-255 range."""
    return (clamp(color[0]), clamp(color[1]), clamp(color[2]))


def lerp_color(color_a: Color, color_b: Color, t: float) -> Color:
    """
    Linear interpolation between two colors.

    Args:
        color_a: Starting color (t=0)
        color_b: Ending color (t=1)
        t: Interpolation factor (0.0 to 1.0)

    Returns:
        Interpolated color

    Example:
        >>> lerp_color((255, 0, 0), (0, 0, 255), 0.5)
        (127, 0, 127)
    """
    t = max(0.0, min(1.0, t))
    return (
        int(color_a[0] + (color_b[0] - color_a[0]) * t),
        int(color_a[1] + (color_b[1] - color_a[1]) * t),
        int(color_a[2] + (color_b[2] - color_a[2]) * t),
    )


def brighten(color: Color, amount: float) -> Color:
    """
    Brighten a color by a factor.

    Args:
        color: The color to brighten
        amount: Brightness increase (0.0 = no change, 1.0 = white)

    Returns:
        Brightened color

    Example:
        >>> brighten((100, 100, 100), 0.5)
        (177, 177, 177)
    """
    return clamp_color((
        int(color[0] + (255 - color[0]) * amount),
        int(color[1] + (255 - color[1]) * amount),
        int(color[2] + (255 - color[2]) * amount),
    ))


def darken(color: Color, amount: float) -> Color:
    """
    Darken a color by a factor.

    Args:
        color: The color to darken
        amount: Darkness increase (0.0 = no change, 1.0 = black)

    Returns:
        Darkened color

    Example:
        >>> darken((200, 200, 200), 0.5)
        (100, 100, 100)
    """
    return clamp_color((
        int(color[0] * (1.0 - amount)),
        int(color[1] * (1.0 - amount)),
        int(color[2] * (1.0 - amount)),
    ))


def multiply_color(color: Color, factor: float) -> Color:
    """
    Multiply a color by a scalar factor.

    Args:
        color: The color to multiply
        factor: Multiplication factor

    Returns:
        Multiplied color (clamped to valid range)
    """
    return clamp_color((
        int(color[0] * factor),
        int(color[1] * factor),
        int(color[2] * factor),
    ))


def add_colors(color_a: Color, color_b: Color) -> Color:
    """
    Add two colors together (additive blending).

    Args:
        color_a: First color
        color_b: Second color

    Returns:
        Sum of colors (clamped to valid range)
    """
    return clamp_color((
        color_a[0] + color_b[0],
        color_a[1] + color_b[1],
        color_a[2] + color_b[2],
    ))


# Common color constants
BLACK: Color = (0, 0, 0)
WHITE: Color = (255, 255, 255)
RED: Color = (255, 0, 0)
GREEN: Color = (0, 255, 0)
BLUE: Color = (0, 0, 255)
YELLOW: Color = (255, 255, 0)
CYAN: Color = (0, 255, 255)
MAGENTA: Color = (255, 0, 255)
ORANGE: Color = (255, 165, 0)
GRAY: Color = (128, 128, 128)
DARK_GRAY: Color = (64, 64, 64)
LIGHT_GRAY: Color = (192, 192, 192)
