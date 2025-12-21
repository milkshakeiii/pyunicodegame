"""
pyunicodegame.layers.layer - Layer class for compositing.

QUICK START:
    from pyunicodegame.layers import Layer

    background = Layer(z_index=0, name="background")
    entities = Layer(z_index=10, name="entities")
    ui = Layer(z_index=100, name="ui")

CLASSES:
    Layer: A single rendering layer with visibility and alpha

Layers allow separating different elements (background, entities, effects, UI)
for independent manipulation and compositing.
"""

from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING

import pygame

from ..core.colors import Color
from ..core.grid import Grid

if TYPE_CHECKING:
    pass


@dataclass
class Layer:
    """
    A single layer in the rendering stack.

    Each layer contains its own grid and can be independently controlled
    for visibility, opacity, and blending.

    Attributes:
        name: Identifier for this layer
        z_index: Sorting order (higher = rendered on top)
        width: Grid width in cells
        height: Grid height in cells
        visible: Whether this layer is rendered
        alpha: Opacity from 0.0 (transparent) to 1.0 (opaque)
        grid: The cell grid for this layer
    """
    name: str = "layer"
    z_index: int = 0
    width: int = 80
    height: int = 25
    visible: bool = True
    alpha: float = 1.0
    default_bg: Optional[Color] = None
    grid: Grid = field(init=False)
    _surface: Optional[pygame.Surface] = field(default=None, init=False, repr=False)
    _dirty: bool = field(default=True, init=False)

    def __post_init__(self):
        """Initialize the grid after dataclass init."""
        self.grid = Grid(self.width, self.height, self.default_bg)

    def put(
        self,
        x: int,
        y: int,
        char: str,
        fg: Color = (255, 255, 255),
        bg: Optional[Color] = None,
        glow: float = 0.0,
        glow_color: Optional[Color] = None,
    ) -> bool:
        """
        Put a character on this layer.

        Args:
            x: X coordinate
            y: Y coordinate
            char: Character to draw
            fg: Foreground color
            bg: Background color
            glow: Glow intensity
            glow_color: Override glow color

        Returns:
            True if the cell was modified
        """
        result = self.grid.put(x, y, char, fg, bg, glow, glow_color)
        if result:
            self._dirty = True
        return result

    def put_string(
        self,
        x: int,
        y: int,
        text: str,
        fg: Color = (255, 255, 255),
        bg: Optional[Color] = None,
        glow: float = 0.0,
    ) -> int:
        """
        Put a string on this layer.

        Args:
            x: Starting X coordinate
            y: Y coordinate
            text: String to draw
            fg: Foreground color
            bg: Background color
            glow: Glow intensity

        Returns:
            Number of characters written
        """
        result = self.grid.put_string(x, y, text, fg, bg, glow)
        if result > 0:
            self._dirty = True
        return result

    def fill(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        char: str = " ",
        fg: Color = (255, 255, 255),
        bg: Optional[Color] = None,
    ) -> None:
        """Fill a region on this layer."""
        self.grid.fill(x, y, width, height, char, fg, bg)
        self._dirty = True

    def clear(self, bg: Optional[Color] = None) -> None:
        """Clear the entire layer."""
        self.grid.clear(bg)
        self._dirty = True

    def mark_dirty(self) -> None:
        """Mark the layer as needing re-render."""
        self._dirty = True
        self.grid.mark_all_dirty()

    def is_dirty(self) -> bool:
        """Check if the layer needs re-rendering."""
        return self._dirty or self.grid.needs_redraw()

    def mark_clean(self) -> None:
        """Mark the layer as rendered."""
        self._dirty = False
        self.grid.mark_clean()
