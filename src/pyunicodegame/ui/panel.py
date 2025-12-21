"""
pyunicodegame.ui.panel - Panel/window components.

QUICK START:
    from pyunicodegame.ui import Panel, BorderStyle

    panel = Panel(
        x=5, y=2,
        width=30, height=10,
        title="Status",
        border_style=BorderStyle.single()
    )
    panel.draw(renderer)

    # Write content relative to panel interior
    panel.put_string(renderer, 0, 0, "HP: 100/100", fg=(0, 255, 0))

CLASSES:
    Panel: A bordered window/panel with optional title

Panels provide a convenient way to create bordered regions with
automatic content area management.
"""

from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING, Tuple

from .borders import BorderStyle
from ..core.colors import Color

if TYPE_CHECKING:
    from ..core.renderer import Renderer


@dataclass
class Panel:
    """
    A bordered panel/window component.

    Panels manage a rectangular region with borders and an optional title.
    They track their content area (interior) for easy relative positioning.

    Attributes:
        x: Left edge position
        y: Top edge position
        width: Total width including borders
        height: Total height including borders
        title: Optional title text displayed on top border
        border_style: Box-drawing character configuration
        border_fg: Border foreground color
        border_bg: Border background color
        fill_bg: Interior fill background color
        title_fg: Title text color
        padding: Interior padding from border
    """
    x: int
    y: int
    width: int
    height: int
    title: Optional[str] = None
    border_style: BorderStyle = field(default_factory=BorderStyle.single)
    border_fg: Optional[Color] = None
    border_bg: Optional[Color] = None
    fill_bg: Optional[Color] = None
    title_fg: Optional[Color] = None
    padding: int = 0

    @property
    def inner_x(self) -> int:
        """X coordinate of the content area."""
        return self.x + 1 + self.padding

    @property
    def inner_y(self) -> int:
        """Y coordinate of the content area."""
        return self.y + 1 + self.padding

    @property
    def inner_width(self) -> int:
        """Width of the content area."""
        return max(0, self.width - 2 - self.padding * 2)

    @property
    def inner_height(self) -> int:
        """Height of the content area."""
        return max(0, self.height - 2 - self.padding * 2)

    @property
    def inner_rect(self) -> Tuple[int, int, int, int]:
        """Get the content area as (x, y, width, height)."""
        return (self.inner_x, self.inner_y, self.inner_width, self.inner_height)

    def draw(self, renderer: "Renderer") -> None:
        """
        Draw the panel to the renderer.

        This draws the border, fills the interior, and renders the title.

        Args:
            renderer: The Renderer to draw to
        """
        # Get colors from theme if not specified
        border_fg = self.border_fg
        if border_fg is None and renderer.theme:
            border_fg = renderer.theme.panel_border
        if border_fg is None:
            border_fg = (128, 128, 128)

        fill_bg = self.fill_bg
        if fill_bg is None and renderer.theme:
            fill_bg = renderer.theme.panel_bg

        title_fg = self.title_fg
        if title_fg is None and renderer.theme:
            title_fg = renderer.theme.panel_title
        if title_fg is None:
            title_fg = (255, 255, 100)

        # Draw corners
        renderer.put(self.x, self.y, self.border_style.top_left, border_fg, self.border_bg)
        renderer.put(self.x + self.width - 1, self.y, self.border_style.top_right, border_fg, self.border_bg)
        renderer.put(self.x, self.y + self.height - 1, self.border_style.bottom_left, border_fg, self.border_bg)
        renderer.put(self.x + self.width - 1, self.y + self.height - 1, self.border_style.bottom_right, border_fg, self.border_bg)

        # Draw horizontal edges
        for dx in range(1, self.width - 1):
            renderer.put(self.x + dx, self.y, self.border_style.horizontal, border_fg, self.border_bg)
            renderer.put(self.x + dx, self.y + self.height - 1, self.border_style.horizontal, border_fg, self.border_bg)

        # Draw vertical edges
        for dy in range(1, self.height - 1):
            renderer.put(self.x, self.y + dy, self.border_style.vertical, border_fg, self.border_bg)
            renderer.put(self.x + self.width - 1, self.y + dy, self.border_style.vertical, border_fg, self.border_bg)

        # Fill interior
        if self.width > 2 and self.height > 2:
            renderer.fill(
                self.x + 1,
                self.y + 1,
                self.width - 2,
                self.height - 2,
                " ",
                border_fg,
                fill_bg
            )

        # Draw title
        if self.title and self.width > 4:
            # Truncate title if too long
            max_title_len = self.width - 4
            display_title = self.title
            if len(display_title) > max_title_len:
                display_title = display_title[:max_title_len - 1] + "\u2026"  # Ellipsis

            # Center the title on top border
            title_x = self.x + (self.width - len(display_title)) // 2
            renderer.put_string(title_x, self.y, display_title, title_fg, self.border_bg)

    def put(
        self,
        renderer: "Renderer",
        x: int,
        y: int,
        char: str,
        fg: Optional[Color] = None,
        bg: Optional[Color] = None,
        glow: float = 0.0,
    ) -> bool:
        """
        Put a character relative to the panel's content area.

        Args:
            renderer: The Renderer to draw to
            x: X position relative to content area
            y: Y position relative to content area
            char: Character to draw
            fg: Foreground color
            bg: Background color
            glow: Glow intensity

        Returns:
            True if the character was drawn (within bounds)
        """
        if 0 <= x < self.inner_width and 0 <= y < self.inner_height:
            return renderer.put(self.inner_x + x, self.inner_y + y, char, fg, bg, glow)
        return False

    def put_string(
        self,
        renderer: "Renderer",
        x: int,
        y: int,
        text: str,
        fg: Optional[Color] = None,
        bg: Optional[Color] = None,
        glow: float = 0.0,
    ) -> int:
        """
        Put a string relative to the panel's content area.

        The string is clipped to the content area bounds.

        Args:
            renderer: The Renderer to draw to
            x: X position relative to content area
            y: Y position relative to content area
            text: String to draw
            fg: Foreground color
            bg: Background color
            glow: Glow intensity

        Returns:
            Number of characters drawn
        """
        if y < 0 or y >= self.inner_height:
            return 0

        # Clip to content area
        if x < 0:
            text = text[-x:]
            x = 0

        if x >= self.inner_width:
            return 0

        # Truncate to fit
        max_len = self.inner_width - x
        if len(text) > max_len:
            text = text[:max_len]

        return renderer.put_string(
            self.inner_x + x,
            self.inner_y + y,
            text,
            fg,
            bg,
            glow
        )

    def fill_content(
        self,
        renderer: "Renderer",
        char: str = " ",
        fg: Optional[Color] = None,
        bg: Optional[Color] = None,
    ) -> None:
        """
        Fill the entire content area with a character.

        Args:
            renderer: The Renderer to draw to
            char: Character to fill with
            fg: Foreground color
            bg: Background color
        """
        renderer.fill(
            self.inner_x,
            self.inner_y,
            self.inner_width,
            self.inner_height,
            char,
            fg,
            bg
        )

    def clear_content(self, renderer: "Renderer") -> None:
        """Clear the content area (fill with spaces using fill_bg)."""
        self.fill_content(renderer, " ", None, self.fill_bg)
