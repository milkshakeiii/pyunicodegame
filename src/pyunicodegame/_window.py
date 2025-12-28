"""Window class for pyunicodegame."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, List, Optional, Tuple, Union

import pygame
import pygame.freetype

if TYPE_CHECKING:
    from ._sprites import EffectSpriteEmitter, Sprite


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
        self._sprites: List[Union[Sprite, "EffectSpriteEmitter"]] = []
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
        self._lightmap: Optional[List[List[List[int]]]] = None  # [y][x][rgb]

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
        return light

    def remove_light(self, light) -> None:
        """Remove a light source from this window."""
        if light in self._lights:
            self._lights.remove(light)

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

    def _build_blocking_set(self) -> set:
        """Build set of cells that block light from sprites."""
        blocking = set()

        for sprite in self._sprites:
            if not getattr(sprite, 'blocks_light', False):
                continue

            # Get sprite's current cell position
            sx, sy = int(sprite.x), int(sprite.y)
            if not sprite.frames:
                continue
            frame = sprite.frames[sprite.current_frame]

            # Add all non-space cells of the sprite as blockers
            for row_idx, row in enumerate(frame.chars):
                for col_idx, char in enumerate(row):
                    if char != ' ':
                        cx = sx + col_idx - sprite.origin[0]
                        cy = sy + row_idx - sprite.origin[1]
                        blocking.add((cx, cy))

        return blocking

    def _compute_lightmap(self) -> None:
        """Compute the light map from all lights."""
        from ._lighting import compute_visible_cells

        # Initialize light map to ambient
        self._lightmap = [
            [[self._ambient[0], self._ambient[1], self._ambient[2]]
             for _ in range(self.width)]
            for _ in range(self.height)
        ]

        if not self._lights:
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

            # Accumulate light for visible cells
            for (cx, cy) in visible:
                if 0 <= cx < self.width and 0 <= cy < self.height:
                    # Calculate distance falloff
                    dx = cx - light.x
                    dy = cy - light.y
                    distance = math.sqrt(dx * dx + dy * dy)

                    if distance < light.radius:
                        attenuation = 1.0 - (distance / light.radius) ** light.falloff
                        brightness = attenuation * light.intensity

                        # Accumulate light color
                        self._lightmap[cy][cx][0] += int(light.color[0] * brightness)
                        self._lightmap[cy][cx][1] += int(light.color[1] * brightness)
                        self._lightmap[cy][cx][2] += int(light.color[2] * brightness)

        # Clamp to valid range
        for y in range(self.height):
            for x in range(self.width):
                for c in range(3):
                    self._lightmap[y][x][c] = min(255, self._lightmap[y][x][c])

    def _apply_lighting(self) -> None:
        """Apply the light map to the window surface."""
        if self._lightmap is None:
            return

        # Use surfarray for efficient pixel access
        try:
            pixels = pygame.surfarray.pixels3d(self.surface)
        except pygame.error:
            return  # Surface doesn't support pixel access

        # Apply light map cell by cell
        for y in range(self.height):
            for x in range(self.width):
                light = self._lightmap[y][x]

                # Get pixel region for this cell
                px1 = x * self._cell_width
                px2 = px1 + self._cell_width
                py1 = y * self._cell_height
                py2 = py1 + self._cell_height

                # Clamp to surface bounds
                px2 = min(px2, pixels.shape[0])
                py2 = min(py2, pixels.shape[1])

                # Multiply RGB by light color (normalized)
                for c in range(3):
                    factor = light[c] / 255.0
                    pixels[px1:px2, py1:py2, c] = (
                        pixels[px1:px2, py1:py2, c] * factor
                    ).astype('uint8')

        del pixels  # Unlock surface
