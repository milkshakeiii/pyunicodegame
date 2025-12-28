"""Lighting system for pyunicodegame."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Optional, Tuple

import pygame

if TYPE_CHECKING:
    from ._sprites import Sprite


class Light:
    """
    A point light source with color, radius, and optional shadow casting.

    Lights illuminate cells within their radius, with brightness falling off
    based on distance. When shadow casting is enabled, sprites marked with
    blocks_light=True will cast shadows.

    Attributes:
        x, y: Position in cell coordinates
        radius: Maximum light radius in cells
        color: RGB light color (tints illuminated cells)
        intensity: Brightness multiplier (0.0 to 1.0+)
        falloff: Distance falloff exponent (1=linear, 2=quadratic)
        casts_shadows: Whether blockers cast shadows from this light
        follow_sprite: If set, light position follows sprite's position
    """

    def __init__(
        self,
        x: float,
        y: float,
        radius: float = 10.0,
        color: Tuple[int, int, int] = (255, 255, 255),
        intensity: float = 1.0,
        falloff: float = 1.0,
        casts_shadows: bool = True,
        follow_sprite: Optional[Sprite] = None,
    ):
        """
        Create a light source.

        Args:
            x, y: Position in cell coordinates
            radius: Maximum light radius in cells
            color: RGB light color (tints illuminated cells)
            intensity: Brightness multiplier
            falloff: Distance falloff exponent (1=linear, 2=quadratic)
            casts_shadows: Whether blockers cast shadows from this light
            follow_sprite: If set, light position follows sprite's position
        """
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        self.intensity = intensity
        self.falloff = falloff
        self.casts_shadows = casts_shadows
        self.follow_sprite = follow_sprite

    def move_to(self, x: float, y: float) -> None:
        """Move the light to a new position."""
        self.x = x
        self.y = y


def compute_visible_cells(
    origin_x: int,
    origin_y: int,
    radius: float,
    is_blocking: Callable[[int, int], bool],
) -> set:
    """
    Compute visible cells from origin using symmetric shadowcasting.

    Args:
        origin_x, origin_y: Light source position
        radius: Maximum visibility radius
        is_blocking: Function that returns True if cell blocks light

    Returns:
        Set of (x, y) tuples for visible cells
    """
    visible = {(origin_x, origin_y)}

    # Process each octant
    for octant in range(8):
        _scan_octant(
            origin_x, origin_y, radius, octant, 1,
            1.0, 0.0,  # start_slope, end_slope
            is_blocking, visible
        )

    return visible


def _scan_octant(
    ox: int, oy: int, radius: float, octant: int, row: int,
    start_slope: float, end_slope: float,
    is_blocking: Callable[[int, int], bool],
    visible: set,
) -> None:
    """Scan one octant for visible cells using recursive shadowcasting."""
    if start_slope < end_slope:
        return

    next_start_slope = start_slope

    for j in range(row, int(radius) + 1):
        blocked = False

        for dx in range(-j, 1):
            # Map dx, j to actual coordinates based on octant
            dy = -j
            nx, ny = _transform_octant(ox, oy, dx, dy, octant)

            # Calculate slopes for this cell
            left_slope = (dx - 0.5) / (dy + 0.5)
            right_slope = (dx + 0.5) / (dy - 0.5)

            if start_slope < right_slope:
                continue
            if end_slope > left_slope:
                break

            # Check if cell is within radius
            dist_sq = dx * dx + j * j
            if dist_sq <= radius * radius:
                visible.add((nx, ny))

            # Handle blocking
            if blocked:
                if is_blocking(nx, ny):
                    next_start_slope = right_slope
                else:
                    blocked = False
                    start_slope = next_start_slope
            elif is_blocking(nx, ny) and j < radius:
                blocked = True
                _scan_octant(
                    ox, oy, radius, octant, j + 1,
                    start_slope, left_slope,
                    is_blocking, visible
                )
                next_start_slope = right_slope

        if blocked:
            break


def _transform_octant(ox: int, oy: int, dx: int, dy: int, octant: int) -> Tuple[int, int]:
    """Transform local octant coordinates to world coordinates."""
    if octant == 0:
        return ox + dx, oy + dy
    elif octant == 1:
        return ox + dy, oy + dx
    elif octant == 2:
        return ox + dy, oy - dx
    elif octant == 3:
        return ox + dx, oy - dy
    elif octant == 4:
        return ox - dx, oy - dy
    elif octant == 5:
        return ox - dy, oy - dx
    elif octant == 6:
        return ox - dy, oy + dx
    else:  # octant == 7
        return ox - dx, oy + dy


def apply_bloom(
    surface: pygame.Surface,
    threshold: int = 200,
    blur_scale: int = 4,
    intensity: float = 1.0,
    emissive_surface: Optional[pygame.Surface] = None,
) -> None:
    """
    Apply bloom post-processing effect to a surface (in-place).

    Args:
        surface: The surface to apply bloom to (modified in-place)
        threshold: Brightness cutoff (0-255)
        blur_scale: Downscale factor for blur effect (higher = bigger glow)
        intensity: Bloom brightness multiplier (higher = brighter glow)
        emissive_surface: Optional surface of emissive-only content (bypasses threshold)
    """
    size = surface.get_size()
    if size[0] < 4 or size[1] < 4:
        return  # Surface too small for bloom

    # 1. Extract bright pixels via threshold subtraction
    bright = surface.copy()
    bright.fill((threshold, threshold, threshold), special_flags=pygame.BLEND_RGB_SUB)

    # 2. Add emissive content (bypasses threshold)
    if emissive_surface is not None:
        bright.blit(emissive_surface, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

    # 3. Multi-pass blur at increasing scales for bigger, layered glow
    # Each pass adds to the bloom, creating a richer effect
    blurred = pygame.Surface(size, pygame.SRCALPHA)
    blurred.fill((0, 0, 0, 0))

    # Do passes at scales 2, 4, 8... up to blur_scale
    scale = 2
    while scale <= blur_scale and size[0] // scale >= 1 and size[1] // scale >= 1:
        small_size = (max(1, size[0] // scale), max(1, size[1] // scale))
        small = pygame.transform.smoothscale(bright, small_size)
        upscaled = pygame.transform.smoothscale(small, size)
        blurred.blit(upscaled, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        scale *= 2

    # 4. Apply intensity by blitting multiple times
    # intensity 1.0 = 1 blit, 2.0 = 2 blits, etc.
    if intensity <= 0:
        return

    # Fractional intensity: dim the surface for partial blits
    full_blits = int(intensity)
    fractional = intensity - full_blits

    for _ in range(full_blits):
        surface.blit(blurred, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

    if fractional > 0:
        # Apply fractional intensity
        frac_val = int(255 * fractional)
        frac_surface = blurred.copy()
        frac_surface.fill((frac_val, frac_val, frac_val), special_flags=pygame.BLEND_RGB_MULT)
        surface.blit(frac_surface, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
