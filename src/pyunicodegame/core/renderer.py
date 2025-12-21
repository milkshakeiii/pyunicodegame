"""
pyunicodegame.core.renderer - Main Renderer class for TUI graphics.

QUICK START:
    import pygame
    import pyunicodegame

    pygame.init()
    screen = pygame.display.set_mode((800, 600))

    renderer = pyunicodegame.Renderer(width=80, height=25, scale=2)

    renderer.clear()
    renderer.put(10, 5, "@", fg=(0, 255, 0), glow=0.5)
    renderer.put_string(0, 0, "Hello, World!")
    renderer.render(screen)

    pygame.display.flip()

CLASSES:
    Renderer: The main interface for all rendering operations

The Renderer orchestrates the Grid, GlyphCache, and effects systems
to provide a simple, unified API for TUI-style graphics.
"""

from typing import Optional, List, Tuple, TYPE_CHECKING

import pygame

from .colors import Color
from .grid import Grid, Cell
from .glyph_cache import GlyphCache

if TYPE_CHECKING:
    from ..effects.particles import ParticleSystem
    from ..effects.animation import Animation
    from ..effects.bloom import BloomProcessor
    from ..themes.theme import Theme
    from ..ui.borders import BorderStyle


class Renderer:
    """
    The main interface for TUI-style rendering with pygame.

    The Renderer manages a grid of cells, a glyph cache for efficient
    sprite rendering, and optional effects like bloom and particles.

    Attributes:
        width: Grid width in cells
        height: Grid height in cells
        grid: The underlying Grid buffer
        glyph_cache: Cache for rendered character sprites
        pixel_width: Total width in pixels
        pixel_height: Total height in pixels
    """

    def __init__(
        self,
        width: int,
        height: int,
        font_path: Optional[str] = None,
        scale: int = 1,
        theme: Optional["Theme"] = None,
        enable_bloom: bool = True,
        default_bg: Optional[Color] = None,
    ):
        """
        Initialize the renderer.

        Args:
            width: Grid width in cells
            height: Grid height in cells
            font_path: Path to BDF font (None = bundled default)
            scale: Integer scaling factor for sprites
            theme: Color theme (None = default theme)
            enable_bloom: Whether to enable glow/bloom effects
            default_bg: Default background color for the grid
        """
        self.width = width
        self.height = height

        # Initialize glyph cache first to get tile dimensions
        self.glyph_cache = GlyphCache(font_path, scale)

        # Calculate pixel dimensions
        self.pixel_width = width * self.glyph_cache.tile_width
        self.pixel_height = height * self.glyph_cache.tile_height

        # Initialize grid
        self.grid = Grid(width, height, default_bg)

        # Theme
        self._theme = theme

        # Effects
        self._enable_bloom = enable_bloom
        self._bloom_processor: Optional["BloomProcessor"] = None
        self._particle_systems: List["ParticleSystem"] = []
        self._animations: List["Animation"] = []

        # Render surface
        self._surface = pygame.Surface(
            (self.pixel_width, self.pixel_height),
            pygame.SRCALPHA
        )

        # Glow surface for bloom effect
        self._glow_surface: Optional[pygame.Surface] = None
        if enable_bloom:
            self._glow_surface = pygame.Surface(
                (self.pixel_width, self.pixel_height),
                pygame.SRCALPHA
            )

    @property
    def theme(self) -> Optional["Theme"]:
        """Get the current theme."""
        return self._theme

    @theme.setter
    def theme(self, value: Optional["Theme"]) -> None:
        """Set the theme and mark grid for redraw."""
        self._theme = value
        self.grid.mark_all_dirty()

    @property
    def tile_width(self) -> int:
        """Width of a single tile in pixels."""
        return self.glyph_cache.tile_width

    @property
    def tile_height(self) -> int:
        """Height of a single tile in pixels."""
        return self.glyph_cache.tile_height

    # -------------------------------------------------------------------------
    # Grid operations
    # -------------------------------------------------------------------------

    def put(
        self,
        x: int,
        y: int,
        char: str,
        fg: Optional[Color] = None,
        bg: Optional[Color] = None,
        glow: float = 0.0,
        glow_color: Optional[Color] = None,
    ) -> bool:
        """
        Draw a character at the given grid position.

        Args:
            x: X coordinate (column)
            y: Y coordinate (row)
            char: Character to draw
            fg: Foreground color (None = white or theme default)
            bg: Background color (None = transparent)
            glow: Glow intensity (0.0 to 1.0)
            glow_color: Override color for glow (None = use fg)

        Returns:
            True if the cell was modified.
        """
        if fg is None:
            fg = self._theme.foreground if self._theme else (255, 255, 255)
        return self.grid.put(x, y, char, fg, bg, glow, glow_color)

    def put_string(
        self,
        x: int,
        y: int,
        text: str,
        fg: Optional[Color] = None,
        bg: Optional[Color] = None,
        glow: float = 0.0,
    ) -> int:
        """
        Draw a string starting at the given position.

        Args:
            x: Starting X coordinate
            y: Y coordinate
            text: String to draw
            fg: Foreground color
            bg: Background color
            glow: Glow intensity

        Returns:
            Number of characters written.
        """
        if fg is None:
            fg = self._theme.foreground if self._theme else (255, 255, 255)
        return self.grid.put_string(x, y, text, fg, bg, glow)

    def fill(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        char: str = " ",
        fg: Optional[Color] = None,
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
        if fg is None:
            fg = self._theme.foreground if self._theme else (255, 255, 255)
        self.grid.fill(x, y, width, height, char, fg, bg)

    def clear(self, bg: Optional[Color] = None) -> None:
        """
        Clear the entire grid.

        Args:
            bg: Background color (None = use theme or default)
        """
        if bg is None and self._theme:
            bg = self._theme.background
        self.grid.clear(bg)

    def get_cell(self, x: int, y: int) -> Optional[Cell]:
        """Get the cell at the given position."""
        return self.grid.get(x, y)

    # -------------------------------------------------------------------------
    # Panel/box drawing
    # -------------------------------------------------------------------------

    def draw_box(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        border_style: Optional["BorderStyle"] = None,
        fg: Optional[Color] = None,
        bg: Optional[Color] = None,
        fill: bool = True,
    ) -> None:
        """
        Draw a box using box-drawing characters.

        Args:
            x: Left edge
            y: Top edge
            width: Box width (including borders)
            height: Box height (including borders)
            border_style: Border characters to use
            fg: Border foreground color
            bg: Background color for border and fill
            fill: Whether to fill the interior
        """
        from ..ui.borders import BorderStyle

        if border_style is None:
            border_style = BorderStyle.single()
        if fg is None:
            fg = self._theme.panel_border if self._theme else (128, 128, 128)

        # Corners
        self.put(x, y, border_style.top_left, fg, bg)
        self.put(x + width - 1, y, border_style.top_right, fg, bg)
        self.put(x, y + height - 1, border_style.bottom_left, fg, bg)
        self.put(x + width - 1, y + height - 1, border_style.bottom_right, fg, bg)

        # Horizontal edges
        for dx in range(1, width - 1):
            self.put(x + dx, y, border_style.horizontal, fg, bg)
            self.put(x + dx, y + height - 1, border_style.horizontal, fg, bg)

        # Vertical edges
        for dy in range(1, height - 1):
            self.put(x, y + dy, border_style.vertical, fg, bg)
            self.put(x + width - 1, y + dy, border_style.vertical, fg, bg)

        # Fill interior
        if fill and width > 2 and height > 2:
            fill_bg = bg if bg else (self._theme.panel_bg if self._theme else None)
            self.fill(x + 1, y + 1, width - 2, height - 2, " ", fg, fill_bg)

    def draw_panel(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        title: Optional[str] = None,
        border_style: Optional["BorderStyle"] = None,
        border_fg: Optional[Color] = None,
        title_fg: Optional[Color] = None,
        bg: Optional[Color] = None,
    ) -> None:
        """
        Draw a panel with optional title.

        Args:
            x: Left edge
            y: Top edge
            width: Panel width
            height: Panel height
            title: Optional title text
            border_style: Border characters to use
            border_fg: Border color
            title_fg: Title text color
            bg: Background color
        """
        # Draw the box
        self.draw_box(x, y, width, height, border_style, border_fg, bg)

        # Draw title if provided
        if title and width > 4:
            if title_fg is None:
                title_fg = self._theme.panel_title if self._theme else (255, 255, 100)

            # Truncate title if too long
            max_title_len = width - 4
            if len(title) > max_title_len:
                title = title[:max_title_len - 1] + "\u2026"  # Ellipsis

            # Center the title
            title_x = x + (width - len(title)) // 2
            self.put_string(title_x, y, title, title_fg, bg)

    # -------------------------------------------------------------------------
    # Effects
    # -------------------------------------------------------------------------

    def spawn_particles(self, system: "ParticleSystem") -> None:
        """
        Add a particle system to be updated and rendered.

        Args:
            system: The particle system to add
        """
        self._particle_systems.append(system)

    def add_animation(self, animation: "Animation") -> None:
        """
        Add an animation to be updated each frame.

        Args:
            animation: The animation to add
        """
        self._animations.append(animation)

    def set_bloom_processor(self, processor: "BloomProcessor") -> None:
        """Set a custom bloom processor."""
        self._bloom_processor = processor

    # -------------------------------------------------------------------------
    # Update and render
    # -------------------------------------------------------------------------

    def update(self, dt: float) -> None:
        """
        Update animations and particle systems.

        Call this once per frame with the delta time.

        Args:
            dt: Time since last frame in seconds
        """
        # Update animations
        self._animations = [a for a in self._animations if a.update(dt)]

        # Update particle systems
        alive_systems = []
        for system in self._particle_systems:
            system.update(dt)
            if system.is_alive():
                alive_systems.append(system)
        self._particle_systems = alive_systems

    def render(
        self,
        target: pygame.Surface,
        offset: Tuple[int, int] = (0, 0),
    ) -> None:
        """
        Render the grid to a pygame surface.

        Args:
            target: The surface to render to
            offset: Pixel offset for rendering position
        """
        # If there are active particles, we need a full redraw since
        # particles render on top of the grid and move around
        if self._particle_systems:
            self.grid.mark_all_dirty()

        # Render grid cells
        self._render_grid()

        # Apply bloom effect if enabled and there are glowing cells
        if self._enable_bloom and self._glow_surface:
            self._render_glow()
            if self._bloom_processor:
                self._surface = self._bloom_processor.process(
                    self._surface,
                    self._glow_surface
                )
            else:
                # Simple additive blend for basic glow
                self._surface.blit(
                    self._glow_surface,
                    (0, 0),
                    special_flags=pygame.BLEND_RGB_ADD
                )

        # Render particles on top
        self._render_particles()

        # Blit to target
        target.blit(self._surface, offset)

        # Mark grid as clean
        self.grid.mark_clean()

    def _render_grid(self) -> None:
        """Render all dirty cells to the internal surface."""
        dirty_cells = self.grid.get_dirty_cells()

        # Determine the default background color for clearing cells
        default_bg = self.grid.default_bg
        if default_bg is None and self._theme:
            default_bg = self._theme.background
        if default_bg is None:
            default_bg = (0, 0, 0)

        for x, y in dirty_cells:
            cell = self.grid.cells[y][x]
            px = x * self.tile_width
            py = y * self.tile_height

            # Clear the cell area first with background color
            # This prevents old content from showing through transparent sprites
            cell_bg = cell.bg if cell.bg is not None else default_bg
            cell_rect = pygame.Rect(px, py, self.tile_width, self.tile_height)
            self._surface.fill(cell_bg, cell_rect)

            # Get sprite (handles caching internally)
            sprite = self.glyph_cache.get_sprite(cell.char, cell.fg, None)

            # Blit to surface
            self._surface.blit(sprite, (px, py))

    def _render_glow(self) -> None:
        """Render glowing cells to the glow surface."""
        if not self._glow_surface:
            return

        # Clear to black (not transparent) for additive blending
        self._glow_surface.fill((0, 0, 0))

        for y in range(self.height):
            for x in range(self.width):
                cell = self.grid.cells[y][x]
                if cell.glow > 0:
                    glow_color = cell.glow_color or cell.fg
                    glow_sprite = self.glyph_cache.get_glow_sprite(
                        cell.char,
                        glow_color,
                        cell.glow
                    )

                    # Center the glow sprite (it has padding)
                    sprite_w = glow_sprite.get_width()
                    sprite_h = glow_sprite.get_height()
                    offset_x = (sprite_w - self.tile_width) // 2
                    offset_y = (sprite_h - self.tile_height) // 2

                    px = x * self.tile_width - offset_x
                    py = y * self.tile_height - offset_y

                    # Additive blend so overlapping glows combine smoothly
                    self._glow_surface.blit(
                        glow_sprite, (px, py),
                        special_flags=pygame.BLEND_RGB_ADD
                    )

    def _render_particles(self) -> None:
        """Render all active particle systems."""
        for system in self._particle_systems:
            for particle in system.get_particles():
                # Convert float coords to grid coords
                gx = int(particle.x)
                gy = int(particle.y)

                if 0 <= gx < self.width and 0 <= gy < self.height:
                    # Calculate fade
                    alpha = 1.0
                    if particle.fade and particle.lifetime > 0:
                        alpha = 1.0 - (particle.age / particle.lifetime)
                        alpha = max(0.0, min(1.0, alpha))

                    # Get sprite with faded color
                    faded_color = (
                        int(particle.color[0] * alpha),
                        int(particle.color[1] * alpha),
                        int(particle.color[2] * alpha),
                    )

                    sprite = self.glyph_cache.get_sprite(
                        particle.char,
                        faded_color,
                        None
                    )

                    px = gx * self.tile_width
                    py = gy * self.tile_height
                    self._surface.blit(sprite, (px, py))

    def create_surface(self) -> pygame.Surface:
        """
        Create a new pygame surface sized for this renderer.

        Useful for creating off-screen buffers.

        Returns:
            A new pygame.Surface with the renderer's pixel dimensions.
        """
        return pygame.Surface(
            (self.pixel_width, self.pixel_height),
            pygame.SRCALPHA
        )
