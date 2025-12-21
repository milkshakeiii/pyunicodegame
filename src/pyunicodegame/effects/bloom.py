"""
pyunicodegame.effects.bloom - Glow/bloom post-processing effects.

QUICK START:
    from pyunicodegame.effects.bloom import BloomProcessor

    processor = BloomProcessor(intensity=1.5, blur_passes=3)
    result = processor.process(base_surface, glow_surface)

CLASSES:
    BloomProcessor: Applies bloom/glow post-processing

The bloom effect works by:
1. Extracting bright/glowing areas into a separate surface
2. Downsampling and blurring the glow surface
3. Upsampling and additively blending with the original

This creates a soft glow around bright elements.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

import pygame


class BloomQuality(Enum):
    """Quality presets for bloom processing."""
    LOW = 1      # Fast, minimal blur
    MEDIUM = 2   # Balanced
    HIGH = 3     # Best quality, more blur passes


@dataclass
class BloomProcessor:
    """
    Post-processing bloom/glow effect.

    Applies a bloom effect by blurring glowing elements and
    additively blending them back onto the base image.

    Attributes:
        intensity: Overall bloom brightness (0.0 to 2.0+)
        blur_passes: Number of blur iterations
        downsample: Downscale factor for blur (1 = no downscale)
        quality: Quality preset affecting blur behavior
    """
    intensity: float = 1.0
    blur_passes: int = 3
    downsample: int = 2
    quality: BloomQuality = BloomQuality.MEDIUM

    def __post_init__(self):
        """Initialize internal surfaces."""
        self._blur_surface: Optional[pygame.Surface] = None

    def process(
        self,
        base_surface: pygame.Surface,
        glow_surface: pygame.Surface,
    ) -> pygame.Surface:
        """
        Apply bloom effect to a surface.

        Args:
            base_surface: The main rendered image
            glow_surface: Surface containing only glowing elements

        Returns:
            New surface with bloom applied
        """
        if self.intensity <= 0:
            return base_surface

        width = glow_surface.get_width()
        height = glow_surface.get_height()

        # Downsample for faster blur
        small_w = max(1, width // self.downsample)
        small_h = max(1, height // self.downsample)

        # Use smoothscale for bilinear filtering
        small = pygame.transform.smoothscale(glow_surface, (small_w, small_h))

        # Apply blur passes
        for _ in range(self.blur_passes):
            small = self._box_blur(small)

        # Upsample back to original size
        blurred = pygame.transform.smoothscale(small, (width, height))

        # Apply intensity
        if self.intensity != 1.0:
            blurred = self._apply_intensity(blurred)

        # Composite result
        result = base_surface.copy()
        result.blit(blurred, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

        return result

    def _box_blur(self, surface: pygame.Surface) -> pygame.Surface:
        """
        Apply a simple box blur by scaling down and up.

        This is a fast approximation of Gaussian blur using
        pygame's built-in scaling with bilinear interpolation.
        """
        w = surface.get_width()
        h = surface.get_height()

        # Scale down
        small_w = max(1, w // 2)
        small_h = max(1, h // 2)
        small = pygame.transform.smoothscale(surface, (small_w, small_h))

        # Scale back up
        return pygame.transform.smoothscale(small, (w, h))

    def _apply_intensity(self, surface: pygame.Surface) -> pygame.Surface:
        """Apply intensity multiplier to a surface."""
        if self.intensity >= 1.0:
            # Brighten by blitting multiple times
            result = surface.copy()
            times = int(self.intensity)
            remainder = self.intensity - times

            for _ in range(times - 1):
                result.blit(surface, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

            if remainder > 0:
                # Create a dimmed version for partial intensity
                temp = surface.copy()
                temp.set_alpha(int(255 * remainder))
                result.blit(temp, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

            return result
        else:
            # Dim by setting alpha
            result = surface.copy()
            result.set_alpha(int(255 * self.intensity))

            temp = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            temp.blit(result, (0, 0))
            return temp

    def create_glow_map(
        self,
        cells: list,
        glyph_cache,
        width: int,
        height: int,
        tile_width: int,
        tile_height: int,
    ) -> pygame.Surface:
        """
        Create a glow map from grid cells.

        This is a utility method that can be used by the Renderer
        to extract glowing cells into a separate surface.

        Args:
            cells: 2D list of Cell objects
            glyph_cache: GlyphCache for rendering
            width: Grid width in cells
            height: Grid height in cells
            tile_width: Tile width in pixels
            tile_height: Tile height in pixels

        Returns:
            Surface containing only glowing elements
        """
        pixel_width = width * tile_width
        pixel_height = height * tile_height

        glow_surface = pygame.Surface(
            (pixel_width, pixel_height),
            pygame.SRCALPHA
        )
        glow_surface.fill((0, 0, 0, 0))

        for y, row in enumerate(cells):
            for x, cell in enumerate(row):
                if cell.glow > 0:
                    glow_color = cell.glow_color or cell.fg
                    glow_sprite = glyph_cache.get_glow_sprite(
                        cell.char,
                        glow_color,
                        cell.glow * self.intensity
                    )

                    # Center the padded glow sprite
                    sprite_w = glow_sprite.get_width()
                    sprite_h = glow_sprite.get_height()
                    offset_x = (sprite_w - tile_width) // 2
                    offset_y = (sprite_h - tile_height) // 2

                    px = x * tile_width - offset_x
                    py = y * tile_height - offset_y

                    glow_surface.blit(glow_sprite, (px, py))

        return glow_surface


def create_radial_gradient(
    width: int,
    height: int,
    color: tuple,
    center: Optional[tuple] = None,
    radius: Optional[float] = None,
) -> pygame.Surface:
    """
    Create a radial gradient surface for custom glow effects.

    Args:
        width: Surface width
        height: Surface height
        color: RGB color for the gradient
        center: Center point (default = surface center)
        radius: Gradient radius (default = half diagonal)

    Returns:
        Surface with radial gradient
    """
    import math

    surface = pygame.Surface((width, height), pygame.SRCALPHA)

    if center is None:
        center = (width // 2, height // 2)

    if radius is None:
        radius = math.sqrt(width ** 2 + height ** 2) / 2

    for y in range(height):
        for x in range(width):
            dx = x - center[0]
            dy = y - center[1]
            dist = math.sqrt(dx * dx + dy * dy)

            # Calculate alpha based on distance from center
            if dist >= radius:
                alpha = 0
            else:
                alpha = int(255 * (1 - dist / radius))

            surface.set_at((x, y), (color[0], color[1], color[2], alpha))

    return surface
