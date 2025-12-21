"""
pyunicodegame.core.glyph_cache - Efficient caching of rendered character sprites.

QUICK START:
    from pyunicodegame.core.glyph_cache import GlyphCache

    cache = GlyphCache()  # Uses bundled font
    sprite = cache.get_sprite("@", (0, 255, 0))
    screen.blit(sprite, (x * cache.tile_width, y * cache.tile_height))

CLASSES:
    GlyphCache: Caches rendered character sprites for efficient reuse

The cache uses a dictionary keyed by (character, fg_color, bg_color) tuples
to avoid re-rendering the same glyph multiple times.
"""

import math
from typing import Dict, Optional, Tuple

import pygame
import pygame.freetype

from .colors import Color
from .fonts import load_font, get_font_dimensions


class GlyphCache:
    """
    Caches rendered character sprites for efficient rendering.

    Each unique combination of (character, foreground, background) is
    rendered once and cached for reuse. This dramatically improves
    performance when rendering large grids.

    Attributes:
        font: The pygame.freetype.Font object
        tile_width: Width of each tile in pixels
        tile_height: Height of each tile in pixels
        scale: Integer scaling factor
    """

    def __init__(
        self,
        font_path: Optional[str] = None,
        scale: int = 1,
    ):
        """
        Initialize the glyph cache.

        Args:
            font_path: Path to a BDF font file. None uses bundled default.
            scale: Integer scaling factor for sprites (1 = native size)
        """
        self.scale = scale
        self.font = load_font(font_path)

        # Get base tile dimensions from font
        base_width, base_height = get_font_dimensions(self.font)
        self.tile_width = base_width * scale
        self.tile_height = base_height * scale

        # Cache storage
        self._cache: Dict[
            Tuple[str, Color, Optional[Color]],
            pygame.Surface
        ] = {}

        # Glow cache (separate for glow sprites)
        self._glow_cache: Dict[
            Tuple[str, Color, float],
            pygame.Surface
        ] = {}

    def get_sprite(
        self,
        char: str,
        fg: Color,
        bg: Optional[Color] = None,
    ) -> pygame.Surface:
        """
        Get a cached sprite for a character with the given colors.

        If the sprite isn't cached, it will be rendered and stored.

        Args:
            char: Single character to render
            fg: Foreground color
            bg: Background color (None = transparent)

        Returns:
            A pygame.Surface containing the rendered character.
        """
        key = (char, fg, bg)
        if key in self._cache:
            return self._cache[key]

        # Render the character
        text_surf, _ = self.font.render(char, fg, bg)

        # Scale if needed
        if self.scale != 1:
            text_surf = pygame.transform.scale_by(text_surf, self.scale)

        self._cache[key] = text_surf
        return text_surf

    def get_glow_sprite(
        self,
        char: str,
        color: Color,
        intensity: float = 1.0,
        radius: int = 4,
    ) -> pygame.Surface:
        """
        Get a soft circular glow effect sprite.

        Creates a circular radial gradient glow centered on the tile.
        Intensity controls both the size and brightness of the glow.

        Args:
            char: Single character (used for cache key, glow is circular)
            color: Glow color
            intensity: Glow brightness and size (0.0 to 1.0)
            radius: Base radius multiplier

        Returns:
            A pygame.Surface with the circular glow effect.
        """
        # Round intensity to 2 decimal places for cache efficiency
        intensity = round(intensity, 2)
        key = (char, color, intensity, radius)

        if key in self._glow_cache:
            return self._glow_cache[key]

        # Size scales with intensity - larger glow for higher intensity
        base_radius = max(self.tile_width, self.tile_height) * self.scale
        glow_radius = int(base_radius * (1.0 + intensity * 1.8))  # Range: 1.0x to 2.8x
        glow_radius = max(glow_radius, 10)

        # Create surface
        surf_size = glow_radius * 2
        glow_surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)

        # Use PixelArray for direct pixel access
        pixels = pygame.PixelArray(glow_surf)
        center = surf_size // 2
        # For additive blending, we premultiply alpha into RGB
        max_brightness = 0.3 * intensity  # 0 to 0.3 range for subtle glow

        for y in range(surf_size):
            for x in range(surf_size):
                # Calculate distance from center
                dx = x - center
                dy = y - center
                dist = math.sqrt(dx * dx + dy * dy)

                if dist < glow_radius:
                    # Normalized distance (0 at center, 1 at edge)
                    t = dist / glow_radius
                    # Steep falloff so brightness is near-zero at the edge
                    falloff = math.exp(-t * t * t * 4.0)
                    brightness = max_brightness * falloff

                    if brightness > 0.01:
                        # Premultiply color by brightness for additive blend
                        r = int(color[0] * brightness)
                        g = int(color[1] * brightness)
                        b = int(color[2] * brightness)
                        pixels[x, y] = (r, g, b, 255)

        del pixels  # Release PixelArray to unlock surface

        self._glow_cache[key] = glow_surf
        return glow_surf

    def clear_cache(self) -> None:
        """Clear all cached sprites."""
        self._cache.clear()
        self._glow_cache.clear()

    def preload_ascii(self, fg: Color = (255, 255, 255)) -> None:
        """
        Pre-render common ASCII characters to warm up the cache.

        Args:
            fg: Foreground color to use for preloading
        """
        for code in range(32, 127):
            self.get_sprite(chr(code), fg)

    def get_cache_stats(self) -> Tuple[int, int]:
        """
        Get cache statistics.

        Returns:
            Tuple of (regular_cache_size, glow_cache_size)
        """
        return len(self._cache), len(self._glow_cache)
