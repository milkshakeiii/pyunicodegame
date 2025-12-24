"""
pyunicodegame - A pygame library for TUI-style unicode graphics.

QUICK START:
    import pyunicodegame

    def update(dt):
        pass  # Game logic here

    def render():
        root = pyunicodegame.get_window("root")
        root.put(10, 5, "@", (0, 255, 0))

    def on_key(key):
        pass  # Handle key presses here

    pyunicodegame.init("My Game", width=80, height=25, bg=(20, 20, 30, 255))
    pyunicodegame.run(update=update, render=render, on_key=on_key)

PUBLIC API:
    init(title, width, height, bg) - Initialize pygame, create root window, return it
    run(update, render, on_key) - Run the main game loop
    quit() - Signal the game loop to exit
    create_window(name, x, y, width, height, ..., depth, fixed) - Create a named window
    get_window(name) - Get a window by name ("root" is auto-created)
    remove_window(name) - Remove a window
    create_sprite(pattern, fg, bg, char_colors, z_index, blocks_light, emissive) - Create a sprite from a pattern string
    create_effect(pattern, x, y, vx, vy, ..., z_index) - Create an effect sprite with velocity/drag/fade
    create_emitter(x, y, chars, spawn_rate, ..., z_index) - Create a particle emitter
    create_animation(name, frame_indices, ...) - Create a named animation with offsets
    create_light(x, y, radius, color, ...) - Create a light source with shadows
    set_camera(x, y, mode, depth_scale) - Configure global camera for parallax
    get_camera() - Get camera state (x, y, mode, depth_scale)
    move_camera(dx, dy) - Move camera by relative amount
    Window.set_bloom(enabled, threshold, ...) - Enable bloom post-processing on window
    Window.add_light(light) - Add light to window (auto-enables lighting)
    Window.set_lighting(enabled, ambient) - Configure lighting system
    Window.depth - Parallax depth (0 = at camera, higher = farther)
    Window.fixed - If True, window ignores camera (for UI layers)
    Window.cell_size - Cell dimensions in pixels (width, height)
    Sprite.lerp_speed - Interpolation speed in cells/sec (0 = instant)
    Sprite.move_to(x, y, teleport=False) - Move sprite, teleport=True snaps instantly
    Sprite.emissive / EffectSprite.emissive - Mark sprite to always glow (bypasses threshold)
    Sprite.blocks_light / EffectSprite.blocks_light - Mark sprite to cast shadows
    Sprite.z_index / EffectSprite.z_index - Drawing order within window (higher = on top)
"""

import math
import os
import random
from typing import Callable, Dict, List, Optional, Tuple

import pygame
import pygame.freetype

__version__ = "1.0.0"
__all__ = [
    "init", "run", "quit",
    "create_window", "get_window", "remove_window", "Window",
    "Sprite", "SpriteFrame", "create_sprite",
    "EffectSprite", "create_effect",
    "EffectSpriteEmitter", "create_emitter",
    "Animation", "create_animation",
    "Light", "create_light",
    "set_camera", "get_camera", "move_camera",
]

# Font configuration
FONT_DIR = os.path.join(os.path.dirname(__file__), "fonts")
AVAILABLE_FONTS = {
    "6x13": "6x13.bdf",
    "9x18": "9x18.bdf",
    "10x20": "10x20.bdf",
}
DEFAULT_FONT = "10x20"

# Module state
_fonts: Dict[str, pygame.freetype.Font] = {}
_font_dimensions: Dict[str, Tuple[int, int]] = {}
_root_cell_width: int = 0
_root_cell_height: int = 0
_running: bool = False
_clock: pygame.time.Clock = None
_windows: Dict[str, "Window"] = {}
_fullscreen: bool = False
_windowed_size: Tuple[int, int] = (0, 0)  # Original window size for restoring
_render_surface: pygame.Surface = None  # Off-screen surface for fullscreen scaling

# Camera system
_camera_x: float = 0.0  # Position in pixels
_camera_y: float = 0.0
_camera_mode: str = "orthographic"  # or "perspective"
_camera_depth_scale: float = 0.1  # How much depth affects parallax


def _get_font_dimensions(font: pygame.freetype.Font) -> Tuple[int, int]:
    """Get cell dimensions by rendering a test character."""
    surf, _ = font.render("\u2588", (255, 255, 255))  # Full block character
    return surf.get_width(), surf.get_height()


def _load_font(font_name: str) -> pygame.freetype.Font:
    """Load a font by name, caching for reuse."""
    if font_name in _fonts:
        return _fonts[font_name]

    if font_name not in AVAILABLE_FONTS:
        raise ValueError(f"Unknown font: {font_name}. Available: {list(AVAILABLE_FONTS.keys())}")

    font_path = os.path.join(FONT_DIR, AVAILABLE_FONTS[font_name])
    font = pygame.freetype.Font(font_path)
    _fonts[font_name] = font
    _font_dimensions[font_name] = _get_font_dimensions(font)
    return font


def _toggle_fullscreen() -> None:
    """Toggle between windowed and fullscreen mode, preserving aspect ratio."""
    global _fullscreen, _windowed_size, _render_surface

    _fullscreen = not _fullscreen

    if _fullscreen:
        # Save current window size
        _windowed_size = _render_surface.get_size()

        # Get desktop resolution
        info = pygame.display.Info()
        screen_w, screen_h = info.current_w, info.current_h

        # Switch to fullscreen
        pygame.display.set_mode((screen_w, screen_h), pygame.FULLSCREEN)
    else:
        # Restore windowed mode
        pygame.display.set_mode(_windowed_size)


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
        font_name: str = DEFAULT_FONT,
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
        self._sprites: List["Sprite"] = []
        self._emitters: List["EffectSpriteEmitter"] = []

        # Bloom effect settings
        self._bloom_enabled = False
        self._bloom_threshold = 200
        self._bloom_blur_scale = 4
        self._bloom_intensity = 1.0
        self._emissive_surface: Optional[pygame.Surface] = None

        # Lighting system
        self._lights: List["Light"] = []
        self._lighting_enabled = False
        self._ambient = (30, 30, 40)
        self._lightmap: Optional[List[List[List[int]]]] = None  # [y][x][rgb]

        # Load font and get dimensions
        self._font = _load_font(font_name)
        self._font_name = font_name
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

        # Render character
        if self.scale != 1.0:
            # Render at native size then scale
            surf, _ = self._font.render(char, fg)
            surf = pygame.transform.scale(surf, (self._cell_width, self._cell_height))
        else:
            surf, _ = self._font.render(char, fg)

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

        Args:
            x: Starting cell column
            y: Cell row
            text: String to draw
            fg: Foreground color
            bg: Background color or None
        """
        for i, char in enumerate(text):
            self.put(x + i, y, char, fg, bg)

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

        # Render character
        if self.scale != 1.0:
            surf, _ = self._font.render(char, fg)
            surf = pygame.transform.scale(surf, (self._cell_width, self._cell_height))
        else:
            surf, _ = self._font.render(char, fg)

        # Apply alpha to the character surface
        if alpha < 255:
            surf.set_alpha(alpha)

        self.surface.blit(surf, (px_int, py_int))

    def add_sprite(self, sprite: "Sprite") -> "Sprite":
        """Add a sprite to this window. Returns the sprite for chaining."""
        self._sprites.append(sprite)
        return sprite

    def remove_sprite(self, sprite: "Sprite") -> None:
        """Remove a sprite from this window."""
        if sprite in self._sprites:
            self._sprites.remove(sprite)

    def add_emitter(self, emitter: "EffectSpriteEmitter") -> "EffectSpriteEmitter":
        """Add an emitter to this window. Returns the emitter for chaining."""
        self._emitters.append(emitter)
        return emitter

    def remove_emitter(self, emitter: "EffectSpriteEmitter") -> None:
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

    def add_light(self, light: "Light") -> "Light":
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

    def remove_light(self, light: "Light") -> None:
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
                visible = _compute_visible_cells(
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


class SpriteFrame:
    """
    A single frame of a sprite animation.

    Contains a 2D grid of characters and optional per-character colors.
    """

    def __init__(
        self,
        chars: List[List[str]],
        fg_colors: Optional[List[List[Optional[Tuple[int, int, int]]]]] = None,
        bg_colors: Optional[List[List[Optional[Tuple[int, int, int, int]]]]] = None,
    ):
        """
        Create a sprite frame.

        Args:
            chars: 2D grid of characters (list of rows)
            fg_colors: Optional per-character foreground colors (None = use sprite default)
            bg_colors: Optional per-character background colors (None = use sprite default)
        """
        self.chars = chars
        self.fg_colors = fg_colors
        self.bg_colors = bg_colors
        self.height = len(chars)
        self.width = len(chars[0]) if chars else 0


class Animation:
    """
    A named animation sequence with frame indices and per-frame pixel offsets.

    Animations reference frames by index into a sprite's frames list,
    allowing frame reuse across multiple animations.

    Attributes:
        name: Unique identifier for this animation
        frame_indices: List of indices into the sprite's frames list
        frame_duration: Seconds per frame (controls animation speed)
        offsets: Per-frame pixel offsets as (offset_x, offset_y) tuples
        loop: If True, animation repeats; if False, stays on last frame
        offset_speed: Pixels per second for offset interpolation (0 = instant)
    """

    def __init__(
        self,
        name: str,
        frame_indices: List[int],
        frame_duration: float = 0.1,
        offsets: Optional[List[Tuple[float, float]]] = None,
        loop: bool = True,
        offset_speed: float = 0.0,
    ):
        """
        Create an animation.

        Args:
            name: Unique identifier for this animation
            frame_indices: List of frame indices into sprite.frames
            frame_duration: Seconds per frame
            offsets: Per-frame pixel offsets as (x, y) tuples.
                     Positive x = right, positive y = down.
            loop: If True, animation loops; if False, plays once
            offset_speed: Pixels per second for offset interpolation (0 = instant)
        """
        self.name = name
        self.frame_indices = frame_indices
        self.frame_duration = frame_duration
        self.offsets = offsets if offsets else [(0.0, 0.0)] * len(frame_indices)
        self.loop = loop
        self.offset_speed = offset_speed


class Sprite:
    """
    A unicode sprite - a block of characters that moves as a unit.

    Sprites support smooth movement between cells via interpolation.
    The logical position (x, y) changes instantly on move_to(), while
    the visual position smoothly interpolates toward it.
    """

    def __init__(
        self,
        frames: List[SpriteFrame],
        fg: Tuple[int, int, int] = (255, 255, 255),
        bg: Optional[Tuple[int, int, int, int]] = None,
        origin: Tuple[int, int] = (0, 0),
    ):
        """
        Create a sprite.

        Args:
            frames: List of SpriteFrame objects for animation
            fg: Default foreground color for all characters
            bg: Default background color (None = transparent)
            origin: Offset for positioning (0,0 = top-left of sprite)
        """
        self.frames = frames
        self.fg = fg
        self.bg = bg
        self.origin = origin
        self.current_frame = 0
        self.visible = True

        # Logical position (changes instantly on move_to)
        self.x = 0
        self.y = 0

        # Visual position (private, interpolates toward logical)
        self._visual_x = 0.0  # In pixels
        self._visual_y = 0.0
        self._lerp_speed = 0.0  # Cells per second (0 = instant)
        self._teleport_pending = False  # Flag to force snap on next update

        # Animation system
        self._animations: Dict[str, Animation] = {}
        self._current_animation: Optional[str] = None
        self._animation_frame_index: int = 0
        self._animation_timer: float = 0.0
        self._animation_finished: bool = False

        # Animation offset interpolation in pixels (separate from movement)
        self._target_offset_x: float = 0.0
        self._target_offset_y: float = 0.0
        self._current_offset_x: float = 0.0
        self._current_offset_y: float = 0.0

        # Bloom: if True, always contributes to bloom (bypasses threshold)
        self.emissive = False

        # Lighting: if True, this sprite blocks light (casts shadows)
        self.blocks_light = False

        # Drawing order within window (higher = on top)
        self.z_index = 0

    @property
    def lerp_speed(self) -> float:
        """Interpolation speed in cells per second (0 = instant snap)."""
        return self._lerp_speed

    @lerp_speed.setter
    def lerp_speed(self, value: float) -> None:
        self._lerp_speed = value

    def move_to(self, x: int, y: int, teleport: bool = False) -> None:
        """
        Move the sprite to a new logical position.

        Args:
            x, y: Target position in cells
            teleport: If True, snap visual position instantly (bypass interpolation)

        The logical position always changes instantly. The visual position
        will interpolate toward it based on lerp_speed, unless teleport=True.
        """
        self.x = x
        self.y = y
        if teleport:
            self._teleport_pending = True

    def add_frame(
        self,
        pattern: str,
        fg: Optional[Tuple[int, int, int]] = None,
        char_colors: Optional[Dict[str, Tuple[int, int, int]]] = None,
    ) -> int:
        """
        Add an animation frame from a pattern string.

        Args:
            pattern: Multi-line string defining the frame shape.
                     Spaces are transparent. Leading/trailing blank lines are trimmed.
            fg: Default foreground color for this frame (overrides sprite default)
            char_colors: Optional dict mapping characters to foreground colors

        Returns:
            The index of the newly added frame

        Example:
            player = pyunicodegame.create_sprite('''
                O
               /|\\
               / \\
            ''', fg=(0, 255, 0))

            # Add walk frames with different colors
            player.add_frame('''
                O
               /|\\
               /
            ''', fg=(0, 200, 0))
            player.add_frame('''
                O
               /|\\
                 \\
            ''', fg=(0, 150, 0))
        """
        # Parse pattern (same logic as create_sprite)
        lines = pattern.split('\n')

        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()

        if not lines:
            frame = SpriteFrame([[]])
            self.frames.append(frame)
            return len(self.frames) - 1

        min_indent = float('inf')
        for line in lines:
            if line.strip():
                indent = len(line) - len(line.lstrip())
                min_indent = min(min_indent, indent)

        if min_indent == float('inf'):
            min_indent = 0

        chars = []
        fg_colors = [] if (char_colors or fg) else None
        max_width = 0

        for line in lines:
            if len(line) >= min_indent:
                line = line[int(min_indent):]
            else:
                line = ''

            row = list(line)
            chars.append(row)
            max_width = max(max_width, len(row))

            if char_colors or fg:
                color_row = []
                for c in row:
                    # char_colors takes priority, then fg, then None (use sprite default)
                    if char_colors and c in char_colors:
                        color_row.append(char_colors[c])
                    elif fg:
                        color_row.append(fg)
                    else:
                        color_row.append(None)
                fg_colors.append(color_row)

        for row in chars:
            while len(row) < max_width:
                row.append(' ')

        if fg_colors:
            for row in fg_colors:
                while len(row) < max_width:
                    row.append(None)

        frame = SpriteFrame(chars, fg_colors)
        self.frames.append(frame)
        return len(self.frames) - 1

    def add_animation(self, animation: "Animation") -> None:
        """
        Register an animation with this sprite.

        Args:
            animation: Animation object to add

        Example:
            walk = Animation("walk", [0, 1, 2, 1], frame_duration=0.15,
                             offsets=[(0, 0), (0, -2), (0, 0), (0, -2)])
            sprite.add_animation(walk)
        """
        self._animations[animation.name] = animation

    def play_animation(self, name: str, reset: bool = True) -> None:
        """
        Start playing a named animation.

        Args:
            name: Name of the animation to play
            reset: If True, restart from frame 0; if False, continue from current frame

        Raises:
            KeyError: If no animation with that name exists
        """
        if name not in self._animations:
            raise KeyError(f"No animation named '{name}'")

        if reset or self._current_animation != name:
            self._animation_frame_index = 0
            self._animation_timer = 0.0
            self._animation_finished = False

        self._current_animation = name

        # Set initial frame and offset
        anim = self._animations[name]
        self.current_frame = anim.frame_indices[0]
        self._target_offset_x = anim.offsets[0][0]
        self._target_offset_y = anim.offsets[0][1]

    def stop_animation(self, reset_offset: bool = True) -> None:
        """
        Stop the current animation.

        Args:
            reset_offset: If True, interpolate offset back to (0, 0)
        """
        self._current_animation = None
        self._animation_finished = False
        if reset_offset:
            self._target_offset_x = 0.0
            self._target_offset_y = 0.0

    def is_animation_playing(self, name: Optional[str] = None) -> bool:
        """
        Check if an animation is currently playing.

        Args:
            name: If specified, check if this specific animation is playing.
                  If None, check if any animation is playing.

        Returns:
            True if the animation is playing
        """
        if name is None:
            return self._current_animation is not None and not self._animation_finished
        return self._current_animation == name and not self._animation_finished

    def is_animation_finished(self) -> bool:
        """
        Check if a one-shot animation has completed.

        Returns:
            True if a non-looping animation has reached its last frame
        """
        return self._animation_finished

    def update(self, dt: float, cell_width: int, cell_height: int) -> None:
        """
        Update the sprite's animation, offsets, and visual position.

        Args:
            dt: Delta time in seconds
            cell_width: Width of a cell in pixels
            cell_height: Height of a cell in pixels
        """
        # --- PHASE 1: Animation frame advancement ---
        if self._current_animation and self._current_animation in self._animations:
            anim = self._animations[self._current_animation]

            if not self._animation_finished:
                self._animation_timer += dt

                # Advance frames based on timer
                while self._animation_timer >= anim.frame_duration:
                    self._animation_timer -= anim.frame_duration
                    self._animation_frame_index += 1

                    # Handle end of animation
                    if self._animation_frame_index >= len(anim.frame_indices):
                        if anim.loop:
                            self._animation_frame_index = 0
                        else:
                            self._animation_frame_index = len(anim.frame_indices) - 1
                            self._animation_finished = True
                            break

                # Update current frame from animation
                frame_idx = anim.frame_indices[self._animation_frame_index]
                self.current_frame = frame_idx

                # Update target offset from animation
                offset = anim.offsets[self._animation_frame_index]
                self._target_offset_x = offset[0]
                self._target_offset_y = offset[1]

        # --- PHASE 2: Offset interpolation ---
        anim = self._animations.get(self._current_animation) if self._current_animation else None
        offset_speed = anim.offset_speed if anim else 0.0

        if offset_speed <= 0:
            # Instant offset
            self._current_offset_x = self._target_offset_x
            self._current_offset_y = self._target_offset_y
        else:
            # Smooth interpolation toward target offset
            dx = self._target_offset_x - self._current_offset_x
            dy = self._target_offset_y - self._current_offset_y
            distance = math.sqrt(dx * dx + dy * dy)

            if distance > 0.5:  # Small threshold
                move_dist = min(offset_speed * dt, distance)
                self._current_offset_x += (dx / distance) * move_dist
                self._current_offset_y += (dy / distance) * move_dist
            else:
                self._current_offset_x = self._target_offset_x
                self._current_offset_y = self._target_offset_y

        # --- PHASE 3: Movement interpolation (existing logic) ---
        target_px = self.x * cell_width
        target_py = self.y * cell_height

        if self._lerp_speed <= 0 or self._teleport_pending:
            # Instant movement (snap)
            self._visual_x = float(target_px)
            self._visual_y = float(target_py)
            self._teleport_pending = False
        else:
            dx = target_px - self._visual_x
            dy = target_py - self._visual_y
            distance = math.sqrt(dx * dx + dy * dy)

            if distance > 0.5:  # Small threshold to avoid jitter
                speed_px = self._lerp_speed * cell_width  # cells/sec -> pixels/sec
                move_dist = min(speed_px * dt, distance)
                self._visual_x += (dx / distance) * move_dist
                self._visual_y += (dy / distance) * move_dist
            else:
                self._visual_x = float(target_px)
                self._visual_y = float(target_py)

    def draw(self, window: "Window") -> None:
        """Draw the sprite to a window at its visual position plus animation offset."""
        if not self.frames:
            return

        frame = self.frames[self.current_frame]

        # Calculate pixel position: visual position + animation offset - origin
        base_px = (self._visual_x + self._current_offset_x) - self.origin[0] * window._cell_width
        base_py = (self._visual_y + self._current_offset_y) - self.origin[1] * window._cell_height

        for row_idx, row in enumerate(frame.chars):
            for col_idx, char in enumerate(row):
                if char == ' ':
                    continue  # Transparent

                px = base_px + col_idx * window._cell_width
                py = base_py + row_idx * window._cell_height

                # Determine colors
                fg = self.fg
                if frame.fg_colors and row_idx < len(frame.fg_colors):
                    row_colors = frame.fg_colors[row_idx]
                    if col_idx < len(row_colors) and row_colors[col_idx] is not None:
                        fg = row_colors[col_idx]

                bg = self.bg
                if frame.bg_colors and row_idx < len(frame.bg_colors):
                    row_colors = frame.bg_colors[row_idx]
                    if col_idx < len(row_colors) and row_colors[col_idx] is not None:
                        bg = row_colors[col_idx]

                window._put_at_pixel(px, py, char, fg, bg)


class EffectSprite:
    """
    A visual-only sprite for effects (particles, sparks, explosions, etc.).

    Unlike Sprite, EffectSprite has no logical position - only visual.
    It uses velocity-based movement with optional drag and fade.

    Attributes:
        x, y: Position in cells (float for smooth movement)
        vx, vy: Velocity in cells per second
        drag: Velocity decay per second (0.1 = decays to 10% after 1 sec, 1.0 = no drag)
        fade_time: Seconds until fully transparent (0 = no fade)
        duration: Seconds until death (0 = infinite, use fade_time to control lifetime)
        alive: False when expired (will be auto-removed from window)
    """

    def __init__(
        self,
        frames: List[SpriteFrame],
        fg: Tuple[int, int, int] = (255, 255, 255),
        bg: Optional[Tuple[int, int, int, int]] = None,
        origin: Tuple[int, int] = (0, 0),
    ):
        self.frames = frames
        self.fg = fg
        self.bg = bg
        self.origin = origin
        self.current_frame = 0
        self.visible = True
        self.alive = True

        # Position in cells (float for smooth movement)
        self.x = 0.0
        self.y = 0.0

        # Velocity in cells per second
        self.vx = 0.0
        self.vy = 0.0

        # Drag: velocity multiplier per second (0.1 = decays to 10% after 1 sec)
        self.drag = 1.0  # 1.0 = no drag

        # Fade: seconds until fully transparent (0 = no fade)
        self.fade_time = 0.0
        self._age = 0.0
        self._initial_alpha = 255

        # Duration: seconds until death (0 = infinite, use fade_time)
        self.duration = 0.0

        # Bloom: if True, always contributes to bloom (bypasses threshold)
        self.emissive = False

        # Lighting: if True, this sprite blocks light (casts shadows)
        self.blocks_light = False

        # Drawing order within window (higher = on top)
        self.z_index = 0

    def update(self, dt: float, cell_width: int, cell_height: int) -> None:
        """Update position, velocity, fade, and duration."""
        if not self.alive:
            return

        # Track age
        self._age += dt

        # Apply velocity
        self.x += self.vx * dt
        self.y += self.vy * dt

        # Apply drag (frame-rate independent exponential decay)
        if self.drag < 1.0 and self.drag > 0:
            decay = self.drag ** dt
            self.vx *= decay
            self.vy *= decay

        # Check duration (hard cutoff, no fade)
        if self.duration > 0 and self._age >= self.duration:
            self.alive = False
            self.visible = False
            return

        # Check fade (soft cutoff with alpha transition)
        if self.fade_time > 0 and self._age >= self.fade_time:
            self.alive = False
            self.visible = False

    def draw(self, window: "Window") -> None:
        """Draw the effect sprite with current alpha."""
        if not self.frames or not self.visible:
            return

        # Calculate current alpha based on fade progress
        alpha = self._initial_alpha
        if self.fade_time > 0:
            fade_progress = min(1.0, self._age / self.fade_time)
            alpha = int(self._initial_alpha * (1.0 - fade_progress))

        frame = self.frames[self.current_frame]
        base_px = self.x * window._cell_width - self.origin[0] * window._cell_width
        base_py = self.y * window._cell_height - self.origin[1] * window._cell_height

        for row_idx, row in enumerate(frame.chars):
            for col_idx, char in enumerate(row):
                if char == ' ':
                    continue

                px = base_px + col_idx * window._cell_width
                py = base_py + row_idx * window._cell_height

                # Determine colors
                fg = self.fg
                if frame.fg_colors and row_idx < len(frame.fg_colors):
                    row_colors = frame.fg_colors[row_idx]
                    if col_idx < len(row_colors) and row_colors[col_idx] is not None:
                        fg = row_colors[col_idx]

                bg = self.bg
                if frame.bg_colors and row_idx < len(frame.bg_colors):
                    row_colors = frame.bg_colors[row_idx]
                    if col_idx < len(row_colors) and row_colors[col_idx] is not None:
                        bg = row_colors[col_idx]

                window._put_at_pixel(px, py, char, fg, bg, alpha=alpha)


class EffectSpriteEmitter:
    """
    Continuously spawns EffectSprites at a configurable rate.

    Emitters are attached to a Window via add_emitter() and automatically
    update when the window's update_sprites() is called.

    Attributes:
        x, y: Emitter position in cells
        active: Whether emitter is spawning new particles
        alive: False when emitter is done (duration expired)
    """

    def __init__(
        self,
        x: float,
        y: float,
        # What to spawn
        chars: str = "*",
        colors: Optional[List[Tuple[int, int, int]]] = None,
        # Spawn rate
        spawn_rate: float = 10.0,
        spawn_rate_variance: float = 0.0,
        # Spawn area
        spread: Tuple[float, float] = (0.0, 0.0),
        cell_locked: bool = False,
        # Velocity
        speed: float = 5.0,
        speed_variance: float = 0.0,
        direction: float = 0.0,
        arc: float = 360.0,
        # Particle properties
        drag: float = 1.0,
        fade_time: float = 1.0,
        fade_time_variance: float = 0.0,
        duration: float = 0.0,
        duration_variance: float = 0.0,
        # Emitter lifetime
        emitter_duration: float = 0.0,
        max_particles: int = 100,
        # Particle z-ordering
        z_index: int = 0,
    ):
        """
        Create an effect sprite emitter.

        Args:
            x, y: Emitter position in cells
            chars: Characters to randomly select from for each particle
            colors: Colors to randomly select from (None = white)
            spawn_rate: Particles per second
            spawn_rate_variance: Multiplicative variance (0.2 = ±20%)
            spread: (x, y) random spread in cells from emitter position
            cell_locked: If True, snap spawn positions to cell centers
            speed: Base particle speed in cells/sec
            speed_variance: Multiplicative variance for speed
            direction: Emission direction in degrees (0=right, 90=up)
            arc: Spread angle in degrees (360 = omnidirectional)
            drag: Particle velocity decay per second
            fade_time: Particle fade time in seconds
            fade_time_variance: Multiplicative variance for fade time
            duration: Particle duration in seconds (0 = use fade_time)
            duration_variance: Multiplicative variance for duration
            emitter_duration: How long emitter runs (0 = infinite)
            max_particles: Maximum concurrent particles from this emitter
            z_index: Drawing order for spawned particles (higher = on top)
        """
        self.x = x
        self.y = y
        self.chars = chars
        self.colors = colors if colors else [(255, 255, 255)]
        self.spawn_rate = spawn_rate
        self.spawn_rate_variance = spawn_rate_variance
        self.spread = spread
        self.cell_locked = cell_locked
        self.speed = speed
        self.speed_variance = speed_variance
        self.direction = direction
        self.arc = arc
        self.drag = drag
        self.fade_time = fade_time
        self.fade_time_variance = fade_time_variance
        self.duration = duration
        self.duration_variance = duration_variance
        self.emitter_duration = emitter_duration
        self.max_particles = max_particles
        self.z_index = z_index

        self.active = True
        self.alive = True
        self._age = 0.0
        self._spawn_accumulator = 0.0
        self._spawned_particles: List[EffectSprite] = []

    def _apply_variance(self, value: float, variance: float) -> float:
        """Apply multiplicative variance to a value."""
        if variance <= 0:
            return value
        return value * (1.0 + random.uniform(-variance, variance))

    def update(self, dt: float, window: "Window") -> None:
        """
        Update emitter timer and spawn new particles.

        Args:
            dt: Delta time in seconds
            window: Window to spawn particles into
        """
        if not self.alive:
            return

        self._age += dt

        # Check emitter duration
        if self.emitter_duration > 0 and self._age >= self.emitter_duration:
            self.active = False
            self.alive = False
            return

        if not self.active:
            return

        # Clean up dead particles from our tracking list
        self._spawned_particles = [p for p in self._spawned_particles if p.alive]

        # Calculate current spawn rate with variance
        current_rate = self._apply_variance(self.spawn_rate, self.spawn_rate_variance)
        self._spawn_accumulator += dt * current_rate

        # Spawn particles
        while self._spawn_accumulator >= 1.0 and len(self._spawned_particles) < self.max_particles:
            self._spawn_accumulator -= 1.0
            self._spawn_particle(window)

    def _spawn_particle(self, window: "Window") -> None:
        """Spawn a single particle with randomized properties."""
        # Randomize spawn position
        sx = self.x + random.uniform(-self.spread[0], self.spread[0])
        sy = self.y + random.uniform(-self.spread[1], self.spread[1])
        if self.cell_locked:
            sx = round(sx)
            sy = round(sy)

        # Randomize velocity (direction + arc)
        angle = self.direction + random.uniform(-self.arc / 2, self.arc / 2)
        angle_rad = math.radians(angle)
        spd = self._apply_variance(self.speed, self.speed_variance)
        vx = math.cos(angle_rad) * spd
        vy = -math.sin(angle_rad) * spd  # Negative because y increases downward

        # Randomize properties
        char = random.choice(self.chars)
        color = random.choice(self.colors)
        ft = self._apply_variance(self.fade_time, self.fade_time_variance)
        dur = self._apply_variance(self.duration, self.duration_variance) if self.duration > 0 else 0.0

        # Create particle
        effect = EffectSprite([SpriteFrame([[char]])], color)
        effect.x = sx
        effect.y = sy
        effect.vx = vx
        effect.vy = vy
        effect.drag = self.drag
        effect.fade_time = ft
        effect.duration = dur
        effect.z_index = self.z_index

        # Add to window and track
        window.add_sprite(effect)
        self._spawned_particles.append(effect)

    def stop(self) -> None:
        """Stop spawning new particles (existing particles continue)."""
        self.active = False

    def kill(self) -> None:
        """Stop spawning and mark emitter as dead for removal."""
        self.active = False
        self.alive = False

    def move_to(self, x: float, y: float) -> None:
        """Move the emitter to a new position."""
        self.x = x
        self.y = y


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
        follow_sprite: Optional["Sprite"] = None,
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


def _compute_visible_cells(
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


def _apply_bloom(
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


def create_sprite(
    pattern: str,
    fg: Tuple[int, int, int] = (255, 255, 255),
    bg: Optional[Tuple[int, int, int, int]] = None,
    char_colors: Optional[Dict[str, Tuple[int, int, int]]] = None,
    z_index: int = 0,
    blocks_light: bool = False,
    emissive: bool = False,
    lerp_speed: float = 0.0,
) -> Sprite:
    """
    Create a single-frame sprite from a multi-line string pattern.

    Args:
        pattern: Multi-line string defining the sprite shape.
                 Spaces are transparent. Leading/trailing blank lines are trimmed.
        fg: Default foreground color for all characters
        bg: Default background color (None = transparent)
        char_colors: Optional dict mapping characters to foreground colors
        z_index: Drawing order within window (higher = on top)
        blocks_light: If True, sprite casts shadows in lighting system
        emissive: If True, sprite glows in bloom effect (bypasses threshold)
        lerp_speed: Interpolation speed in cells/sec (0 = instant snap)

    Returns:
        A new Sprite object

    Example:
        player = pyunicodegame.create_sprite('''
            @
           /|\\
           / \\
        ''', fg=(0, 255, 0), char_colors={'@': (255, 255, 0)})
    """
    # Parse pattern into lines, stripping common leading whitespace
    lines = pattern.split('\n')

    # Remove empty leading/trailing lines
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()

    if not lines:
        return Sprite([SpriteFrame([[]])], fg, bg)

    # Find minimum leading whitespace (excluding empty lines)
    min_indent = float('inf')
    for line in lines:
        if line.strip():
            indent = len(line) - len(line.lstrip())
            min_indent = min(min_indent, indent)

    if min_indent == float('inf'):
        min_indent = 0

    # Strip common indent and build char grid
    chars = []
    fg_colors = [] if char_colors else None

    max_width = 0
    for line in lines:
        # Remove common indent
        if len(line) >= min_indent:
            line = line[int(min_indent):]
        else:
            line = ''

        row = list(line)
        chars.append(row)
        max_width = max(max_width, len(row))

        if char_colors:
            color_row = []
            for c in row:
                color_row.append(char_colors.get(c))
            fg_colors.append(color_row)

    # Pad rows to same width
    for row in chars:
        while len(row) < max_width:
            row.append(' ')

    if fg_colors:
        for row in fg_colors:
            while len(row) < max_width:
                row.append(None)

    frame = SpriteFrame(chars, fg_colors)
    sprite = Sprite([frame], fg, bg)
    sprite.z_index = z_index
    sprite.blocks_light = blocks_light
    sprite.emissive = emissive
    sprite.lerp_speed = lerp_speed
    return sprite


def create_effect(
    pattern: str,
    x: float,
    y: float,
    vx: float = 0.0,
    vy: float = 0.0,
    fg: Tuple[int, int, int] = (255, 255, 255),
    bg: Optional[Tuple[int, int, int, int]] = None,
    drag: float = 1.0,
    fade_time: float = 0.0,
    duration: float = 0.0,
    char_colors: Optional[Dict[str, Tuple[int, int, int]]] = None,
    z_index: int = 0,
    blocks_light: bool = False,
) -> EffectSprite:
    """
    Create an effect sprite with velocity, drag, and fade.

    Args:
        pattern: Character(s) for the effect (multi-line string supported)
        x, y: Starting position in cells
        vx, vy: Velocity in cells per second
        fg: Foreground color
        bg: Background color (None = transparent)
        drag: Velocity decay per second (0.1 = decays to 10%/sec, 1.0 = no drag)
        fade_time: Seconds until fully transparent (0 = no fade)
        duration: Seconds until death (0 = infinite, use fade_time)
        char_colors: Optional per-character color overrides
        z_index: Drawing order within window (higher = on top)
        blocks_light: If True, sprite casts shadows in lighting system

    Returns:
        An EffectSprite ready to add to a window

    Example:
        # Create a spark that flies up-right, slows down, and fades out
        spark = pyunicodegame.create_effect('*', x=10, y=15, vx=5, vy=-8,
                                            fg=(255, 200, 0), drag=0.3, fade_time=0.5)
        window.add_sprite(spark)
    """
    # Reuse create_sprite's pattern parsing logic
    lines = pattern.split('\n')

    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()

    if not lines:
        effect = EffectSprite([SpriteFrame([[]])], fg, bg)
        effect.x = x
        effect.y = y
        return effect

    min_indent = float('inf')
    for line in lines:
        if line.strip():
            indent = len(line) - len(line.lstrip())
            min_indent = min(min_indent, indent)

    if min_indent == float('inf'):
        min_indent = 0

    chars = []
    fg_colors = [] if char_colors else None
    max_width = 0

    for line in lines:
        if len(line) >= min_indent:
            line = line[int(min_indent):]
        else:
            line = ''

        row = list(line)
        chars.append(row)
        max_width = max(max_width, len(row))

        if char_colors:
            color_row = []
            for c in row:
                color_row.append(char_colors.get(c))
            fg_colors.append(color_row)

    for row in chars:
        while len(row) < max_width:
            row.append(' ')

    if fg_colors:
        for row in fg_colors:
            while len(row) < max_width:
                row.append(None)

    frame = SpriteFrame(chars, fg_colors)
    effect = EffectSprite([frame], fg, bg)
    effect.x = x
    effect.y = y
    effect.vx = vx
    effect.vy = vy
    effect.drag = drag
    effect.fade_time = fade_time
    effect.duration = duration
    effect.z_index = z_index
    effect.blocks_light = blocks_light
    return effect


def create_animation(
    name: str,
    frame_indices: List[int],
    frame_duration: float = 0.1,
    offsets: Optional[List[Tuple[float, float]]] = None,
    loop: bool = True,
    offset_speed: float = 0.0,
) -> Animation:
    """
    Create an Animation object.

    Args:
        name: Unique identifier for this animation
        frame_indices: List of frame indices into sprite.frames
        frame_duration: Seconds per frame
        offsets: Per-frame pixel offsets as (x, y) tuples.
                 Positive x = right, positive y = down.
        loop: If True, animation loops; if False, plays once
        offset_speed: Pixels per second for offset interpolation (0 = instant)

    Returns:
        Animation object ready to add to a sprite

    Example:
        # Walking animation with bobbing offset
        walk = pyunicodegame.create_animation(
            "walk",
            frame_indices=[0, 1, 2, 1],
            frame_duration=0.12,
            offsets=[(0, 0), (0, -3), (0, 0), (0, -3)],
            loop=True,
            offset_speed=100.0
        )
        player.add_animation(walk)
        player.play_animation("walk")
    """
    return Animation(name, frame_indices, frame_duration, offsets, loop, offset_speed)


def create_emitter(
    x: float,
    y: float,
    chars: str = "*",
    colors: Optional[List[Tuple[int, int, int]]] = None,
    spawn_rate: float = 10.0,
    spawn_rate_variance: float = 0.0,
    spread: Tuple[float, float] = (0.0, 0.0),
    cell_locked: bool = False,
    speed: float = 5.0,
    speed_variance: float = 0.0,
    direction: float = 0.0,
    arc: float = 360.0,
    drag: float = 1.0,
    fade_time: float = 1.0,
    fade_time_variance: float = 0.0,
    duration: float = 0.0,
    duration_variance: float = 0.0,
    emitter_duration: float = 0.0,
    max_particles: int = 100,
    z_index: int = 0,
) -> EffectSpriteEmitter:
    """
    Create an effect sprite emitter.

    Args:
        x, y: Emitter position in cells
        chars: Characters to randomly select from
        colors: Colors to randomly select from (None = white)
        spawn_rate: Particles per second
        spawn_rate_variance: Multiplicative variance (0.2 = ±20%)
        spread: (x, y) random spread in cells
        cell_locked: Snap spawn positions to cell centers
        speed: Particle speed in cells/sec
        speed_variance: Multiplicative variance for speed
        direction: Emission direction in degrees (0=right, 90=up)
        arc: Spread angle in degrees (360 = omnidirectional)
        drag: Particle velocity decay per second
        fade_time: Particle fade time in seconds
        fade_time_variance: Multiplicative variance for fade time
        duration: Particle duration (0 = use fade_time)
        duration_variance: Multiplicative variance for duration
        emitter_duration: How long emitter runs (0 = infinite)
        max_particles: Maximum concurrent particles
        z_index: Drawing order for spawned particles (higher = on top)

    Returns:
        EffectSpriteEmitter ready to add to a window

    Example:
        # Smoke rising from position (10, 20)
        smoke = pyunicodegame.create_emitter(
            x=10, y=20,
            chars=".oO",
            colors=[(100, 100, 100), (120, 120, 120)],
            spawn_rate=5,
            speed=2, direction=90, arc=30,
            fade_time=2.0,
        )
        window.add_emitter(smoke)
    """
    return EffectSpriteEmitter(
        x=x, y=y,
        chars=chars, colors=colors,
        spawn_rate=spawn_rate, spawn_rate_variance=spawn_rate_variance,
        spread=spread, cell_locked=cell_locked,
        speed=speed, speed_variance=speed_variance,
        direction=direction, arc=arc,
        drag=drag,
        fade_time=fade_time, fade_time_variance=fade_time_variance,
        duration=duration, duration_variance=duration_variance,
        emitter_duration=emitter_duration, max_particles=max_particles,
        z_index=z_index,
    )


def create_light(
    x: float,
    y: float,
    radius: float = 10.0,
    color: Tuple[int, int, int] = (255, 255, 255),
    intensity: float = 1.0,
    falloff: float = 1.0,
    casts_shadows: bool = True,
    follow_sprite: Optional["Sprite"] = None,
) -> Light:
    """
    Create a light source.

    Adding a light to a window automatically enables the lighting system.
    Lights illuminate cells within their radius, with brightness falling off
    based on distance.

    Args:
        x, y: Position in cell coordinates
        radius: Maximum light radius in cells
        color: RGB light color (tints illuminated cells)
        intensity: Brightness multiplier
        falloff: Distance falloff exponent (1=linear, 2=quadratic)
        casts_shadows: Whether sprites with blocks_light=True cast shadows
        follow_sprite: If set, light position follows sprite's position

    Returns:
        Light ready to add to a window

    Example:
        # Player torch that follows the player
        torch = pyunicodegame.create_light(
            x=10, y=10, radius=12,
            color=(255, 200, 100),  # Warm orange
            follow_sprite=player,
        )
        window.add_light(torch)
    """
    return Light(
        x=x, y=y,
        radius=radius, color=color,
        intensity=intensity, falloff=falloff,
        casts_shadows=casts_shadows,
        follow_sprite=follow_sprite,
    )


def init(
    title: str,
    width: int = 80,
    height: int = 25,
    bg: Optional[Tuple[int, int, int, int]] = None,
) -> "Window":
    """
    Initialize pyunicodegame and pygame, creating a window sized for unicode cells.

    Each cell is 10x20 pixels (from the bundled BDF font). So width=80, height=25
    creates an 800x500 pixel window.

    A root window is automatically created that fills the screen.

    Args:
        title: Window title displayed in the title bar
        width: Grid width in unicode cells (default 80)
        height: Grid height in unicode cells (default 25)
        bg: Root window background color (R, G, B, A), default transparent

    Returns:
        The root Window object

    Example:
        root = pyunicodegame.init("My Game", width=80, height=30, bg=(20, 20, 30, 255))
        # root is now available, or use pyunicodegame.get_window("root")
    """
    global _root_cell_width, _root_cell_height, _clock, _render_surface, _windowed_size

    pygame.init()
    pygame.freetype.init()

    # Load root font and get cell dimensions
    _load_font(DEFAULT_FONT)
    _root_cell_width, _root_cell_height = _font_dimensions[DEFAULT_FONT]

    # Create pygame display
    pixel_width = width * _root_cell_width
    pixel_height = height * _root_cell_height
    pygame.display.set_mode((pixel_width, pixel_height))
    pygame.display.set_caption(title)

    # Create off-screen render surface (used for fullscreen scaling)
    _render_surface = pygame.Surface((pixel_width, pixel_height))
    _windowed_size = (pixel_width, pixel_height)

    _clock = pygame.time.Clock()

    # Create root window automatically
    root = create_window("root", 0, 0, width, height, z_index=0, bg=bg)
    return root


def create_window(
    name: str,
    x: int,
    y: int,
    width: int,
    height: int,
    z_index: int = 0,
    font_name: str = DEFAULT_FONT,
    scale: float = 1.0,
    alpha: int = 255,
    bg: Optional[Tuple[int, int, int, int]] = None,
    depth: float = 0.0,
    fixed: bool = False,
) -> "Window":
    """
    Create a named window for rendering.

    Args:
        name: Unique identifier for this window
        x: X position in root cell coordinates
        y: Y position in root cell coordinates
        width: Width in this window's cells
        height: Height in this window's cells
        z_index: Drawing order (higher = on top, default 0)
        font_name: Font to use ("6x13", "9x18", "10x20")
        scale: Additional scaling factor (default 1.0)
        alpha: Transparency 0-255 (default 255 = opaque)
        bg: Background color (R, G, B, A), default transparent
        depth: Parallax depth (0 = at camera, higher = farther/slower)
        fixed: If True, window ignores camera (for UI layers)

    Returns:
        The created Window object

    Example:
        # Create a background layer with large font
        pyunicodegame.create_window("bg", 0, 0, 40, 15, z_index=0, font_name="10x20", alpha=128)

        # Create a foreground layer with small font
        pyunicodegame.create_window("fg", 0, 0, 80, 30, z_index=10, font_name="6x13")
    """
    window = Window(name, x, y, width, height, z_index, font_name, scale, alpha, bg)
    window.depth = depth
    window.fixed = fixed
    _windows[name] = window
    return window


def get_window(name: str) -> "Window":
    """
    Get a window by name.

    Args:
        name: The window's unique identifier

    Returns:
        The Window object

    Raises:
        KeyError: If no window with that name exists
    """
    return _windows[name]


def remove_window(name: str) -> None:
    """
    Remove a window by name.

    Args:
        name: The window's unique identifier
    """
    if name in _windows:
        del _windows[name]


def run(
    update: Optional[Callable[[float], None]] = None,
    render: Optional[Callable[[], None]] = None,
    on_key: Optional[Callable[[int], None]] = None,
) -> None:
    """
    Run the main game loop.

    Handles events, calls update/render callbacks, and manages timing.
    Loop exits on window close, Escape key, or when quit() is called.

    Sprites are automatically updated and drawn each frame - no manual
    calls needed. If you only use sprites, you may not need render at all.

    Built-in controls:
        - Escape: Exit the game
        - Alt+Enter (Option+Enter on Mac): Toggle fullscreen (aspect-ratio preserved)

    Args:
        update: Called each frame with dt (seconds since last frame). Use for
                game logic like checking animation state or updating positions.
        render: Optional. Called each frame for additional drawing beyond sprites
                (e.g., UI text, ground tiles). Sprites are drawn after this.
        on_key: Called when a key is pressed, with the pygame key code

    Example:
        # Minimal example - sprites only, no callbacks needed
        pyunicodegame.run()

        # With game logic
        def update(dt):
            if player.is_animation_finished():
                player.play_animation("idle")

        def on_key(key):
            if key == pygame.K_SPACE:
                player.play_animation("jump")

        pyunicodegame.run(update=update, on_key=on_key)
    """
    global _running, _fullscreen

    _running = True
    while _running:
        dt = _clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                _running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    _running = False
                elif event.key == pygame.K_RETURN and (event.mod & pygame.KMOD_ALT):
                    # Alt+Enter (Option+Enter on Mac) toggles fullscreen
                    _toggle_fullscreen()
                elif on_key:
                    on_key(event.key)

        if update:
            update(dt)

        # Update all sprites in all windows
        for window in _windows.values():
            window.update_sprites(dt)

        # Clear all windows to their background color
        for window in _windows.values():
            window.surface.fill(window._bg)

        # Call render callback (client draws to windows)
        if render:
            render()

        # Draw all sprites in all windows
        for window in _windows.values():
            window.draw_sprites()

        # Apply lighting to windows that have it enabled
        for window in _windows.values():
            if window._lighting_enabled and window.visible:
                window._compute_lightmap()
                window._apply_lighting()

        # Apply bloom post-processing to windows that have it enabled
        for window in _windows.values():
            if window._bloom_enabled and window.visible:
                _apply_bloom(
                    window.surface,
                    threshold=window._bloom_threshold,
                    blur_scale=window._bloom_blur_scale,
                    intensity=window._bloom_intensity,
                    emissive_surface=window._emissive_surface,
                )

        # Composite all windows in z-order to render surface
        _render_surface.fill((0, 0, 0))
        sorted_windows = sorted(_windows.values(), key=lambda w: w.z_index)
        for window in sorted_windows:
            if not window.visible:
                continue

            # Convert root cell coords to pixels, applying camera
            if window.fixed:
                # Fixed windows ignore camera (for UI)
                px = window.x * _root_cell_width
                py = window.y * _root_cell_height
            elif _camera_mode == "orthographic":
                # Orthographic: all windows move with camera equally
                px = window.x * _root_cell_width - _camera_x
                py = window.y * _root_cell_height - _camera_y
            else:
                # Perspective: depth affects parallax
                factor = 1.0 / (1.0 + window.depth * _camera_depth_scale)
                px = window.x * _root_cell_width - _camera_x * factor
                py = window.y * _root_cell_height - _camera_y * factor

            # Apply alpha
            if window.alpha < 255:
                window.surface.set_alpha(window.alpha)

            _render_surface.blit(window.surface, (int(px), int(py)))

        # Blit render surface to display (with scaling in fullscreen)
        display = pygame.display.get_surface()
        if _fullscreen:
            # Scale to fit display while preserving aspect ratio (letterbox/pillarbox)
            display.fill((0, 0, 0))
            src_w, src_h = _render_surface.get_size()
            dst_w, dst_h = display.get_size()

            # Calculate scaling factor
            scale = min(dst_w / src_w, dst_h / src_h)
            scaled_w = int(src_w * scale)
            scaled_h = int(src_h * scale)

            # Center on screen
            offset_x = (dst_w - scaled_w) // 2
            offset_y = (dst_h - scaled_h) // 2

            scaled = pygame.transform.scale(_render_surface, (scaled_w, scaled_h))
            display.blit(scaled, (offset_x, offset_y))
        else:
            display.blit(_render_surface, (0, 0))

        pygame.display.flip()

    # Reset fullscreen state
    _fullscreen = False

    pygame.quit()


def quit() -> None:
    """
    Signal the game loop to exit.

    Call this from within update or on_key to stop the game.

    Example:
        def on_key(key):
            if key == pygame.K_q:
                pyunicodegame.quit()
    """
    global _running
    _running = False


def set_camera(
    x: float = None,
    y: float = None,
    mode: str = None,
    depth_scale: float = None,
) -> None:
    """
    Configure the global camera.

    In orthographic mode, all windows move with camera 1:1.
    In perspective mode, windows with higher depth values move slower (parallax).

    Args:
        x: Camera X position in pixels (None = unchanged)
        y: Camera Y position in pixels (None = unchanged)
        mode: "orthographic" or "perspective" (None = unchanged)
        depth_scale: How much depth affects parallax (default 0.1, None = unchanged)

    Example:
        # Enable perspective mode for parallax
        pyunicodegame.set_camera(mode="perspective", depth_scale=0.1)

        # Move camera to position
        pyunicodegame.set_camera(x=100, y=50)
    """
    global _camera_x, _camera_y, _camera_mode, _camera_depth_scale
    if x is not None:
        _camera_x = x
    if y is not None:
        _camera_y = y
    if mode is not None:
        if mode not in ("orthographic", "perspective"):
            raise ValueError(f"Invalid camera mode: {mode}. Use 'orthographic' or 'perspective'.")
        _camera_mode = mode
    if depth_scale is not None:
        _camera_depth_scale = depth_scale


def get_camera() -> Tuple[float, float, str, float]:
    """
    Get the current camera state.

    Returns:
        Tuple of (x, y, mode, depth_scale)

    Example:
        x, y, mode, depth_scale = pyunicodegame.get_camera()
    """
    return _camera_x, _camera_y, _camera_mode, _camera_depth_scale


def move_camera(dx: float, dy: float) -> None:
    """
    Move the camera by a relative amount.

    Args:
        dx: Horizontal movement in pixels
        dy: Vertical movement in pixels

    Example:
        # Move camera right
        pyunicodegame.move_camera(5, 0)
    """
    global _camera_x, _camera_y
    _camera_x += dx
    _camera_y += dy
