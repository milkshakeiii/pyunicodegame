"""Window class for pyunicodegame."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, List, Optional, Tuple, Union

import numpy as np
import pygame
import pygame.freetype

if TYPE_CHECKING:
    from ._sprites import EffectSpriteEmitter, PixelEffectSprite, PixelSprite, Sprite


class Window:
    """
    A rendering surface with its own coordinate system and font.

    Windows are composited in z_index order onto the main screen.
    Each window can have a different font size for parallax effects.

    Attributes:
        name: Unique identifier for this window
        x: X position in root cell coordinates
        y: Y position in root cell coordinates
        width: Width in this window's cells
        height: Height in this window's cells
        z_index: Drawing order (higher = on top)
        alpha: Transparency (0-255)
        visible: Whether to draw this window
    """

    def __init__(
        self,
        name: str,
        x: int,
        y: int,
        width: int,
        height: int,
        z_index: int = 0,
        font_name: str = "10x20",
        scale: float = 1.0,
        alpha: int = 255,
        bg: Optional[Tuple[int, int, int, int]] = None,
    ):
        self.name = name
        self.x = x  # Root cell coordinates
        self.y = y
        self.width = width  # In this window's cells
        self.height = height
        self.z_index = z_index
        self.alpha = alpha
        self.scale = scale
        self.visible = True
        self.depth = 0.0  # Parallax depth (0 = at camera plane)
        self.fixed = False  # If True, ignores camera (for UI)
        self._bg = bg if bg is not None else (0, 0, 0, 0)  # Default transparent
        self._sprites: List[Union["Sprite", "PixelSprite", "PixelEffectSprite", "EffectSpriteEmitter"]] = []
        self._emitters: List["EffectSpriteEmitter"] = []

        # Bloom effect settings
        self._bloom_enabled = False
        self._bloom_threshold = 200
        self._bloom_blur_scale = 4
        self._bloom_intensity = 1.0
        self._emissive_surface: Optional[pygame.Surface] = None

        # Lighting system
        from ._lighting import Light
        self._lights: List[Light] = []
        self._lighting_enabled = False
        self._ambient = (30, 30, 40)
        self._lightmap: Optional[np.ndarray] = None  # [y][x][rgb] as float32 array

        # Dirty tracking for lighting optimization
        self._lighting_dirty = True
        self._cached_light_positions: dict = {}  # id(light) -> (x, y)
        self._cached_blocker_positions: set = set()  # set of (sprite_id, x, y)

        # Import font helpers from parent module
        from . import _load_font, _font_dimensions, _get_font_for_char
        self._font = _load_font(font_name)
        self._font_name = font_name
        self._get_font_for_char = _get_font_for_char
        self._cell_width, self._cell_height = _font_dimensions[font_name]

        # Apply scale
        self._cell_width = int(self._cell_width * scale)
        self._cell_height = int(self._cell_height * scale)

        # Create surface
        pixel_width = width * self._cell_width
        pixel_height = height * self._cell_height
        self.surface = pygame.Surface((pixel_width, pixel_height), pygame.SRCALPHA)
        self.surface.fill(self._bg)

    def set_bg(self, color: Tuple[int, int, int, int]) -> None:
        """Set the background color (R, G, B, A)."""
        self._bg = color

    @property
    def cell_size(self) -> Tuple[int, int]:
        """Cell dimensions in pixels (width, height)."""
        return (self._cell_width, self._cell_height)

    def string_width(self, text: str) -> int:
        """
        Return the width of a string in cell units.

        For duospace fonts, wide characters (CJK, etc.) count as 2 cells.
        Useful for centering text or calculating layout.

        Args:
            text: The string to measure

        Returns:
            Width in cells

        Example:
            width = window.string_width("Hello世界")  # Returns 9 for duospace
        """
        total_cells = 0
        for char in text:
            font = self._get_font_for_char(self._font, char)
            metrics = font.get_metrics(char)
            if metrics and metrics[0]:
                char_advance = metrics[0][4]
                cells = round(char_advance / self._cell_width)
                total_cells += max(1, cells)
            else:
                total_cells += 1
        return total_cells

    def put(
        self,
        x: int,
        y: int,
        char: str,
        fg: Tuple[int, int, int] = (255, 255, 255),
        bg: Optional[Tuple[int, int, int]] = None,
    ) -> None:
        """
        Draw a character at cell position (x, y).

        Args:
            x: Cell column
            y: Cell row
            char: Character to draw
            fg: Foreground color (R, G, B)
            bg: Background color (R, G, B) or None for transparent
        """
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return

        px = x * self._cell_width
        py = y * self._cell_height

        # Draw background if specified
        if bg is not None:
            rect = pygame.Rect(px, py, self._cell_width, self._cell_height)
            self.surface.fill((*bg, 255), rect)

        # Render character (select correct font for this char)
        font = self._get_font_for_char(self._font, char)
        if self.scale != 1.0:
            # Render at native size then scale
            surf, _ = font.render(char, fg)
            surf = pygame.transform.scale(surf, (self._cell_width, self._cell_height))
        else:
            surf, _ = font.render(char, fg)

        self.surface.blit(surf, (px, py))

    def put_string(
        self,
        x: int,
        y: int,
        text: str,
        fg: Tuple[int, int, int] = (255, 255, 255),
        bg: Optional[Tuple[int, int, int]] = None,
    ) -> None:
        """
        Draw a string starting at cell position (x, y).

        For duospace fonts (like Unifont), wide characters (CJK, etc.)
        advance the cursor by 2 cells instead of 1.

        Args:
            x: Starting cell column
            y: Cell row
            text: String to draw
            fg: Foreground color
            bg: Background color or None
        """
        cursor = x
        py = y * self._cell_height

        for char in text:
            # Get correct font for this character
            font = self._get_font_for_char(self._font, char)

            # Get actual character width from font metrics
            metrics = font.get_metrics(char)
            if metrics and metrics[0]:
                char_advance = metrics[0][4]  # advance is 5th element
            else:
                char_advance = self._cell_width

            px = cursor * self._cell_width

            # Bounds check
            if cursor >= 0 and cursor < self.width and y >= 0 and y < self.height:
                # Draw background if specified
                if bg is not None:
                    # Background fills the character's actual width
                    char_width_scaled = int(char_advance * self.scale) if self.scale != 1.0 else int(char_advance)
                    rect = pygame.Rect(px, py, char_width_scaled, self._cell_height)
                    self.surface.fill((*bg, 255), rect)

                # Render character
                if self.scale != 1.0:
                    surf, _ = font.render(char, fg)
                    scaled_w = int(char_advance * self.scale)
                    surf = pygame.transform.scale(surf, (scaled_w, self._cell_height))
                else:
                    surf, _ = font.render(char, fg)

                self.surface.blit(surf, (px, py))

            # Advance cursor by character width in cell units
            # (round to nearest cell for duospace: 8px = 1 cell, 16px = 2 cells)
            cells_advance = round(char_advance / self._cell_width)
            cursor += max(1, cells_advance)

    def _put_at_pixel(
        self,
        px: float,
        py: float,
        char: str,
        fg: Tuple[int, int, int],
        bg: Optional[Tuple[int, int, int, int]] = None,
        alpha: int = 255,
    ) -> None:
        """Draw a character at exact pixel coordinates (for sprite interpolation)."""
        px_int = int(px)
        py_int = int(py)

        # Bounds check
        if (px_int < 0 or py_int < 0 or
            px_int >= self.surface.get_width() or py_int >= self.surface.get_height()):
            return

        # Draw background if specified
        if bg is not None:
            rect = pygame.Rect(px_int, py_int, self._cell_width, self._cell_height)
            # Apply alpha to background
            bg_with_alpha = (bg[0], bg[1], bg[2], int(bg[3] * alpha / 255) if len(bg) > 3 else alpha)
            self.surface.fill(bg_with_alpha, rect)

        # Render character (select correct font for this char)
        font = self._get_font_for_char(self._font, char)
        if self.scale != 1.0:
            surf, _ = font.render(char, fg)
            surf = pygame.transform.scale(surf, (self._cell_width, self._cell_height))
        else:
            surf, _ = font.render(char, fg)

        # Apply alpha to the character surface
        if alpha < 255:
            surf.set_alpha(alpha)

        self.surface.blit(surf, (px_int, py_int))

    def add_sprite(self, sprite: Sprite) -> Sprite:
        """Add a sprite to this window. Returns the sprite for chaining."""
        self._sprites.append(sprite)
        return sprite

    def remove_sprite(self, sprite: Sprite) -> None:
        """Remove a sprite from this window."""
        if sprite in self._sprites:
            self._sprites.remove(sprite)

    def add_emitter(self, emitter: EffectSpriteEmitter) -> EffectSpriteEmitter:
        """Add an emitter to this window. Returns the emitter for chaining."""
        self._emitters.append(emitter)
        return emitter

    def remove_emitter(self, emitter: EffectSpriteEmitter) -> None:
        """Remove an emitter from this window."""
        if emitter in self._emitters:
            self._emitters.remove(emitter)

    def update_sprites(self, dt: float) -> None:
        """Update all emitters and sprites, remove dead ones."""
        # Update emitters (may spawn new particles)
        for emitter in self._emitters:
            emitter.update(dt, self)

        # Remove dead emitters
        self._emitters = [e for e in self._emitters if e.alive]

        # Update sprites
        for sprite in self._sprites:
            sprite.update(dt, self._cell_width, self._cell_height)

        # Remove dead EffectSprites
        self._sprites = [s for s in self._sprites
                         if not (hasattr(s, 'alive') and not s.alive)]

    def draw_sprites(self) -> None:
        """Draw all visible sprites to this window (called automatically)."""
        sorted_sprites = sorted(self._sprites, key=lambda s: s.z_index)
        for sprite in sorted_sprites:
            if sprite.visible:
                sprite.draw(self)

        # If bloom is enabled, also draw emissive sprites to emissive surface
        if self._bloom_enabled:
            emissive_sprites = [s for s in sorted_sprites
                                if s.visible and getattr(s, 'emissive', False)]
            if emissive_sprites:
                # Create or resize emissive surface as needed
                if (self._emissive_surface is None or
                    self._emissive_surface.get_size() != self.surface.get_size()):
                    self._emissive_surface = pygame.Surface(
                        self.surface.get_size(), pygame.SRCALPHA
                    )
                self._emissive_surface.fill((0, 0, 0, 0))

                # Temporarily swap surface to draw emissive sprites
                original_surface = self.surface
                self.surface = self._emissive_surface
                for sprite in emissive_sprites:
                    sprite.draw(self)
                self.surface = original_surface
            else:
                # No emissive sprites, clear the surface reference
                self._emissive_surface = None

    def set_bloom(
        self,
        enabled: bool = True,
        threshold: int = 200,
        blur_scale: int = 4,
        intensity: float = 1.0,
    ) -> None:
        """
        Enable or configure bloom effect for this window.

        Bloom creates a soft glow around bright pixels. Sprites marked
        as emissive will always glow regardless of threshold.

        The effect uses multi-pass blurring at increasing scales (2, 4, 8...)
        up to blur_scale, creating a rich layered glow. Intensity controls
        brightness by applying the bloom additively multiple times.

        Args:
            enabled: Whether bloom is active
            threshold: Brightness threshold (0-255). Pixels brighter than this glow.
            blur_scale: Max blur scale (default 4). Higher = bigger glow radius.
                        Uses multi-pass blur at scales 2, 4, 8... up to this value.
            intensity: Bloom brightness multiplier (default 1.0). Higher = brighter.
                       Values > 1.0 apply bloom multiple times additively.

        Example:
            window.set_bloom(enabled=True, threshold=180, blur_scale=8, intensity=2.0)
        """
        self._bloom_enabled = enabled
        self._bloom_threshold = max(0, min(255, threshold))
        self._bloom_blur_scale = max(1, blur_scale)
        self._bloom_intensity = max(0.0, intensity)

    def add_light(self, light) -> "Light":
        """
        Add a light source to this window.

        Adding a light automatically enables the lighting system.

        Args:
            light: The Light object to add

        Returns:
            The light for chaining

        Example:
            torch = pyunicodegame.create_light(x=10, y=10, radius=8)
            window.add_light(torch)
        """
        self._lights.append(light)
        self._lighting_enabled = True
        self._lighting_dirty = True
        return light

    def remove_light(self, light) -> None:
        """Remove a light source from this window."""
        if light in self._lights:
            self._lights.remove(light)
            self._lighting_dirty = True

    def set_lighting(
        self,
        enabled: bool = True,
        ambient: Tuple[int, int, int] = (30, 30, 40),
    ) -> None:
        """
        Configure the lighting system.

        Args:
            enabled: Whether lighting is active
            ambient: RGB color for unlit areas (default dark gray)

        Example:
            window.set_lighting(ambient=(20, 20, 30))  # Darker ambient
            window.set_lighting(enabled=False)  # Disable lighting
        """
        self._lighting_enabled = enabled
        self._ambient = ambient

    def _check_lighting_dirty(self) -> bool:
        """Check if lighting needs recomputation."""
        # Check light positions
        current_light_pos = {id(l): (l.x, l.y) for l in self._lights}
        if current_light_pos != self._cached_light_positions:
            self._cached_light_positions = current_light_pos
            return True

        # Check blocker positions (only sprites that block light)
        current_blockers = set()
        for s in self._sprites:
            if getattr(s, 'blocks_light', False):
                current_blockers.add((id(s), int(s.x), int(s.y)))
        if current_blockers != self._cached_blocker_positions:
            self._cached_blocker_positions = current_blockers
            return True

        return False

    def _build_blocking_set(self) -> set:
        """Build set of cells that block light - only near lights."""
        blocking = set()

        if not self._lights:
            return blocking

        for sprite in self._sprites:
            if not getattr(sprite, 'blocks_light', False):
                continue

            # Get sprite's current cell position
            sx, sy = int(sprite.x), int(sprite.y)

            # Quick check: is sprite near ANY light? (spatial culling)
            near_light = False
            for light in self._lights:
                max_dist = light.radius + 10  # Buffer for sprite size
                if abs(sx - light.x) <= max_dist and abs(sy - light.y) <= max_dist:
                    near_light = True
                    break

            if not near_light:
                continue  # Skip sprites far from all lights

            if not sprite.frames:
                continue
            frame = sprite.frames[sprite.current_frame]

            # Check if this is a PixelSprite/PixelEffectSprite (has surface) or
            # unicode Sprite (has chars)
            if hasattr(frame, 'surface'):
                # PixelSprite: use bounding box based on cell dimensions
                origin = getattr(sprite, 'origin', (0, 0))
                width_cells = frame.width_cells
                height_cells = frame.height_cells
                for row_idx in range(height_cells):
                    for col_idx in range(width_cells):
                        cx = sx + col_idx - origin[0]
                        cy = sy + row_idx - origin[1]
                        blocking.add((cx, cy))
            elif hasattr(frame, 'chars'):
                # Unicode Sprite: add all non-space cells as blockers
                origin = getattr(sprite, 'origin', (0, 0))
                for row_idx, row in enumerate(frame.chars):
                    for col_idx, char in enumerate(row):
                        if char != ' ':
                            cx = sx + col_idx - origin[0]
                            cy = sy + row_idx - origin[1]
                            blocking.add((cx, cy))

        return blocking

    def _compute_lightmap(self) -> None:
        """Compute the light map from all lights using NumPy vectorization."""
        from ._lighting import compute_visible_cells

        # Early exit if nothing changed (dirty tracking)
        if not self._lighting_dirty and not self._check_lighting_dirty():
            return

        # Initialize light map to ambient using NumPy (fast array creation)
        self._lightmap = np.full(
            (self.height, self.width, 3),
            self._ambient,
            dtype=np.float32
        )

        if not self._lights:
            self._lighting_dirty = False
            return

        # Build blocking set once
        blocking = self._build_blocking_set()

        def is_blocking(x: int, y: int) -> bool:
            return (x, y) in blocking

        # Process each light
        for light in self._lights:
            # Update position if following a sprite
            if light.follow_sprite:
                light.x = light.follow_sprite.x
                light.y = light.follow_sprite.y

            origin_x, origin_y = int(light.x), int(light.y)

            # Get visible cells
            if light.casts_shadows:
                visible = compute_visible_cells(
                    origin_x, origin_y, light.radius, is_blocking
                )
            else:
                # No shadows - just use radius
                visible = set()
                r = int(light.radius) + 1
                for dy in range(-r, r + 1):
                    for dx in range(-r, r + 1):
                        if dx * dx + dy * dy <= light.radius * light.radius:
                            visible.add((origin_x + dx, origin_y + dy))

            if not visible:
                continue

            # Vectorized light accumulation
            visible_arr = np.array(list(visible), dtype=np.int32)

            # Filter to valid bounds
            mask = (
                (visible_arr[:, 0] >= 0) & (visible_arr[:, 0] < self.width) &
                (visible_arr[:, 1] >= 0) & (visible_arr[:, 1] < self.height)
            )
            valid = visible_arr[mask]

            if len(valid) == 0:
                continue

            # Calculate distances using squared distance for range check (Phase 4)
            dx = valid[:, 0].astype(np.float32) - light.x
            dy = valid[:, 1].astype(np.float32) - light.y
            dist_sq = dx * dx + dy * dy
            radius_sq = light.radius * light.radius

            # Filter by radius using squared distance
            in_range = dist_sq < radius_sq
            valid = valid[in_range]
            dist_sq = dist_sq[in_range]

            if len(valid) == 0:
                continue

            # Only compute sqrt for cells in range
            distances = np.sqrt(dist_sq)

            # Calculate attenuation
            attenuation = (1.0 - (distances / light.radius)) ** light.falloff
            brightness = attenuation * light.intensity

            # Calculate contribution for each cell
            contribution = np.outer(brightness, np.array(light.color, dtype=np.float32))

            # Accumulate light using np.add.at for in-place addition
            np.add.at(self._lightmap, (valid[:, 1], valid[:, 0]), contribution)

        # Clamp to valid range (vectorized)
        np.clip(self._lightmap, 0, 255, out=self._lightmap)

        self._lighting_dirty = False

    def _apply_lighting(self) -> None:
        """Apply the light map to the window surface using vectorized operations."""
        if self._lightmap is None:
            return

        # Use surfarray for efficient pixel access
        try:
            pixels = pygame.surfarray.pixels3d(self.surface)
        except pygame.error:
            return  # Surface doesn't support pixel access

        # Vectorized approach: expand lightmap from cell to pixel resolution
        # lightmap is [height, width, 3] in cell coordinates
        # pixels is [pixel_width, pixel_height, 3] (note: x, y order for surfarray)

        # Normalize lightmap to 0-1 range
        light_factors = self._lightmap / 255.0

        # Expand from cell resolution to pixel resolution
        # np.repeat along axis 0 (y/height) then axis 1 (x/width)
        expanded = np.repeat(light_factors, self._cell_height, axis=0)
        expanded = np.repeat(expanded, self._cell_width, axis=1)

        # surfarray uses (x, y) order, lightmap uses (y, x) order
        # Transpose to match: from [py, px, 3] to [px, py, 3]
        expanded = np.transpose(expanded, (1, 0, 2))

        # Clip to surface bounds (in case of rounding differences)
        surf_w, surf_h = pixels.shape[0], pixels.shape[1]
        exp_w, exp_h = expanded.shape[0], expanded.shape[1]
        w = min(surf_w, exp_w)
        h = min(surf_h, exp_h)

        # Apply lighting in one vectorized operation
        pixels[:w, :h, :] = (pixels[:w, :h, :] * expanded[:w, :h, :]).astype(np.uint8)

        del pixels  # Unlock surface
