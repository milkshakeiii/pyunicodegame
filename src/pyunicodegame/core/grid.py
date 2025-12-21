"""
pyunicodegame.core.grid - Cell and Grid classes for buffered rendering.

QUICK START:
    from pyunicodegame.core import Cell, Grid

    grid = Grid(80, 25)
    grid.put(10, 5, "@", fg=(0, 255, 0))
    grid.put_string(0, 0, "Hello!", fg=(255, 255, 255))

CLASSES:
    Cell: A single grid cell with character, colors, and glow properties
    Grid: A 2D buffer of cells with dirty tracking for efficient updates

The grid uses a dirty-tracking system to only re-render cells that have
changed, improving performance for large grids.
"""

from dataclasses import dataclass, field
from typing import Optional, Set, Tuple, List

from .colors import Color


@dataclass
class Cell:
    """
    A single cell in the rendering grid.

    Attributes:
        char: The Unicode character to display (single character)
        fg: Foreground color as RGB tuple
        bg: Background color as RGB tuple, or None for transparent
        glow: Glow intensity from 0.0 (none) to 1.0 (maximum)
        glow_color: Override color for glow effect, or None to use fg
        dirty: Whether this cell needs to be re-rendered
    """
    char: str = " "
    fg: Color = (255, 255, 255)
    bg: Optional[Color] = None
    glow: float = 0.0
    glow_color: Optional[Color] = None
    dirty: bool = True

    def set(
        self,
        char: str,
        fg: Color,
        bg: Optional[Color] = None,
        glow: float = 0.0,
        glow_color: Optional[Color] = None,
    ) -> bool:
        """
        Update cell values. Returns True if any value changed.
        """
        changed = (
            self.char != char
            or self.fg != fg
            or self.bg != bg
            or self.glow != glow
            or self.glow_color != glow_color
        )

        if changed:
            self.char = char
            self.fg = fg
            self.bg = bg
            self.glow = glow
            self.glow_color = glow_color
            self.dirty = True

        return changed

    def clear(self, bg: Optional[Color] = None) -> None:
        """Reset cell to empty space."""
        self.set(" ", (255, 255, 255), bg, 0.0, None)


class Grid:
    """
    A 2D buffer of cells for efficient text-based rendering.

    The grid tracks which cells are "dirty" (need re-rendering) to
    minimize the number of draw operations each frame.

    Attributes:
        width: Grid width in cells
        height: Grid height in cells
        cells: 2D list of Cell objects
        dirty_cells: Set of (x, y) coordinates that need re-rendering
    """

    def __init__(self, width: int, height: int, default_bg: Optional[Color] = None):
        """
        Create a new grid buffer.

        Args:
            width: Grid width in cells
            height: Grid height in cells
            default_bg: Default background color for all cells
        """
        self.width = width
        self.height = height
        self.default_bg = default_bg
        self.cells: List[List[Cell]] = [
            [Cell(bg=default_bg) for _ in range(width)]
            for _ in range(height)
        ]
        self.dirty_cells: Set[Tuple[int, int]] = set()
        self._full_redraw = True

    def in_bounds(self, x: int, y: int) -> bool:
        """Check if coordinates are within grid bounds."""
        return 0 <= x < self.width and 0 <= y < self.height

    def get(self, x: int, y: int) -> Optional[Cell]:
        """
        Get the cell at the given coordinates.

        Returns None if out of bounds.
        """
        if not self.in_bounds(x, y):
            return None
        return self.cells[y][x]

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
        Set a cell's contents.

        Args:
            x: X coordinate (column)
            y: Y coordinate (row)
            char: Character to display
            fg: Foreground color
            bg: Background color (None = transparent)
            glow: Glow intensity (0.0 to 1.0)
            glow_color: Override glow color (None = use fg)

        Returns:
            True if the cell was modified, False if out of bounds or unchanged.
        """
        if not self.in_bounds(x, y):
            return False

        cell = self.cells[y][x]
        if cell.set(char, fg, bg, glow, glow_color):
            self.dirty_cells.add((x, y))
            return True
        return False

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
        Write a string starting at the given position.

        Args:
            x: Starting X coordinate
            y: Y coordinate
            text: String to write
            fg: Foreground color
            bg: Background color
            glow: Glow intensity

        Returns:
            Number of characters actually written (may be less if clipped).
        """
        written = 0
        for i, char in enumerate(text):
            if self.put(x + i, y, char, fg, bg, glow):
                written += 1
            elif not self.in_bounds(x + i, y):
                break
        return written

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
        """
        Fill a rectangular region with a character.

        Args:
            x: Left edge
            y: Top edge
            width: Rectangle width
            height: Rectangle height
            char: Character to fill with
            fg: Foreground color
            bg: Background color
        """
        for dy in range(height):
            for dx in range(width):
                self.put(x + dx, y + dy, char, fg, bg)

    def clear(self, bg: Optional[Color] = None) -> None:
        """
        Clear the entire grid.

        Args:
            bg: Background color to fill with (None = use default_bg)
        """
        clear_bg = bg if bg is not None else self.default_bg
        for y in range(self.height):
            for x in range(self.width):
                self.cells[y][x].clear(clear_bg)
                self.dirty_cells.add((x, y))
        self._full_redraw = True

    def get_dirty_cells(self) -> Set[Tuple[int, int]]:
        """
        Get the set of cells that need re-rendering.

        Returns:
            Set of (x, y) tuples for dirty cells.
        """
        if self._full_redraw:
            return {(x, y) for y in range(self.height) for x in range(self.width)}
        return self.dirty_cells.copy()

    def mark_clean(self) -> None:
        """Mark all cells as clean (already rendered)."""
        self.dirty_cells.clear()
        self._full_redraw = False
        for row in self.cells:
            for cell in row:
                cell.dirty = False

    def mark_all_dirty(self) -> None:
        """Mark all cells as needing re-render."""
        self._full_redraw = True

    def needs_redraw(self) -> bool:
        """Check if any cells need re-rendering."""
        return self._full_redraw or len(self.dirty_cells) > 0
