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
    run(update, render, on_key, on_event) - Run the main game loop
    quit() - Signal the game loop to exit
    create_window(name, x, y, width, height, ..., depth, fixed) - Create a named window
    get_window(name) - Get a window by name ("root" is auto-created)
    remove_window(name) - Remove a window
    create_sprite(pattern, x, y, fg, ..., lerp_speed) - Create a sprite at position
    create_sprite_from_image(path, width, height, ...) - Create pixel art sprite from image
    create_effect(pattern, x, y, vx, vy, ..., z_index) - Create an effect sprite with velocity/drag/fade
    create_emitter(x, y, chars, spawn_rate, ..., z_index) - Create a particle emitter
    create_animation(name, frame_indices, ...) - Create a named animation with offsets
    create_light(x, y, radius, color, ...) - Create a light source with shadows
    set_camera(x, y, depth_scale) - Configure global camera for parallax
    get_camera() - Get camera state (x, y, depth_scale)
    move_camera(dx, dy) - Move camera by relative amount
    Window.set_bloom(enabled, threshold, ...) - Enable bloom post-processing on window
    Window.add_light(light) - Add light to window (auto-enables lighting)
    Window.set_lighting(enabled, ambient) - Configure lighting system
    Window.depth - Parallax depth (0 = at camera, higher = farther)
    Window.fixed - If True, window ignores camera (for UI layers)
    Window.cell_size - Cell dimensions in pixels (width, height)
    Window.string_width(text) - Get width of string in cells (handles wide chars)
    Sprite.lerp_speed - Interpolation speed in cells/sec (0 = instant)
    Sprite.move_to(x, y, teleport=False) - Move sprite, teleport=True snaps instantly
    Sprite.emissive / EffectSprite.emissive - Mark sprite to always glow (bypasses threshold)
    Sprite.blocks_light / EffectSprite.blocks_light - Mark sprite to cast shadows
    Sprite.z_index / EffectSprite.z_index - Drawing order within window (higher = on top)
"""

import os
from typing import Callable, Dict, List, Optional, Tuple

import pygame
import pygame.freetype

from ._sprites import Animation, EffectSprite, EffectSpriteEmitter, Sprite, SpriteFrame
from ._lighting import Light, apply_bloom, compute_visible_cells
from ._window import Window

__version__ = "1.0.0"
__all__ = [
    "init", "run", "quit",
    "create_window", "get_window", "remove_window", "Window",
    "Sprite", "SpriteFrame", "create_sprite", "create_sprite_from_image",
    "EffectSprite", "create_effect",
    "EffectSpriteEmitter", "create_emitter",
    "Animation", "create_animation",
    "Light", "create_light",
    "set_camera", "get_camera", "move_camera",
]

# Font configuration
FONT_DIR = os.path.join(os.path.dirname(__file__), "fonts")
AVAILABLE_FONTS = {
    "5x8": "5x8.bdf",
    "6x13": "6x13.bdf",
    "9x18": "9x18.bdf",
    "10x20": "10x20.bdf",
    # Unifont: 8x16 duospace with full Unicode coverage (115K+ chars)
    # Uses two OTF files internally (Plane 0 + Upper planes)
    "unifont": ("unifont.otf", "unifont_upper.otf"),
}
DEFAULT_FONT = "10x20"

# Module state
_fonts: Dict[str, pygame.freetype.Font] = {}
_font_dimensions: Dict[str, Tuple[int, int]] = {}
_root_cell_width: int = 0
_root_cell_height: int = 0
_running: bool = False
_clock: pygame.time.Clock = None
_windows: Dict[str, Window] = {}
_fullscreen: bool = False
_windowed_size: Tuple[int, int] = (0, 0)  # Original window size for restoring
_render_surface: pygame.Surface = None  # Off-screen surface for fullscreen scaling

# Camera system
_camera_x: float = 0.0  # Position in pixels
_camera_y: float = 0.0
_camera_depth_scale: float = 0.1  # How much depth affects parallax


def _get_font_dimensions(font: pygame.freetype.Font) -> Tuple[int, int]:
    """Get base cell dimensions using font metrics (no rendering needed).

    For uniform-width fonts, all characters have the same width.
    For duospace fonts (like Unifont), this returns the narrow (half-width)
    dimension - wide characters will naturally render at ~2x this width.
    """
    # Use get_metrics for the advance width (no surface creation needed)
    metrics = font.get_metrics("M")  # Narrow reference character
    if metrics and metrics[0]:
        width = int(metrics[0][4])  # advance is the 5th element
    else:
        # Fallback to rendering if metrics unavailable
        surf, _ = font.render("M", (255, 255, 255))
        width = surf.get_width()

    # Height from font's sized height (ascender + descender)
    height = font.get_sized_height()

    return width, height


def _get_font_for_char(font_data, char: str) -> pygame.freetype.Font:
    """Return the appropriate font for a character.

    For fonts with fallback (stored as tuple), routes to the correct font
    based on codepoint. Plane 0 (BMP) uses the first font, upper planes
    use the second font.
    """
    if isinstance(font_data, tuple):
        plane0_font, upper_font = font_data
        codepoint = ord(char)
        if codepoint > 0xFFFF:
            return upper_font
        return plane0_font
    return font_data


def _load_font(font_name: str):
    """Load a font by name, caching for reuse.

    Returns a single Font or tuple of (plane0_font, upper_font) for fonts
    with fallback support (like unifont).
    """
    if font_name in _fonts:
        return _fonts[font_name]

    if font_name not in AVAILABLE_FONTS:
        raise ValueError(f"Unknown font: {font_name}. Available: {list(AVAILABLE_FONTS.keys())}")

    font_entry = AVAILABLE_FONTS[font_name]

    if isinstance(font_entry, tuple):
        # Font with fallback - load both files
        plane0_path = os.path.join(FONT_DIR, font_entry[0])
        upper_path = os.path.join(FONT_DIR, font_entry[1])
        plane0_font = pygame.freetype.Font(plane0_path)
        upper_font = pygame.freetype.Font(upper_path)
        # OTF fonts need explicit size; BDF fonts have size pre-set.
        # For pixel fonts like Unifont, derive native size from design height.
        # Assumes 4:1 ratio (design units to pixels) which is common for pixel fonts.
        # Also enable padding so glyphs render with consistent vertical positioning.
        for f in (plane0_font, upper_font):
            if f.size == 0 and f.height > 0:
                f.size = f.height / 4
                f.pad = True
        font_data = (plane0_font, upper_font)
        _fonts[font_name] = font_data
        # Use plane0 font for dimensions (they should be the same)
        _font_dimensions[font_name] = _get_font_dimensions(plane0_font)
        return font_data
    else:
        # Single font file
        font_path = os.path.join(FONT_DIR, font_entry)
        font = pygame.freetype.Font(font_path)
        # OTF fonts need explicit size (assumes 4:1 design units to pixels)
        if font.size == 0 and font.height > 0:
            font.size = font.height / 4
            font.pad = True
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


def create_sprite(
    pattern: str,
    x: int,
    y: int,
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
        x, y: Initial position in cells
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
        ''', x=10, y=5, fg=(0, 255, 0), char_colors={'@': (255, 255, 0)})
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
    sprite.x = x
    sprite.y = y
    sprite._teleport_pending = True  # Snap visual position on first update
    sprite.z_index = z_index
    sprite.blocks_light = blocks_light
    sprite.emissive = emissive
    sprite.lerp_speed = lerp_speed
    return sprite


def create_sprite_from_image(
    image_path: str,
    width: int,
    height: int,
    x: int = 0,
    y: int = 0,
    mode: str = "average",
    transparency_threshold: int = 240,
    z_index: int = 0,
    blocks_light: bool = False,
    emissive: bool = False,
    lerp_speed: float = 0.0,
) -> Sprite:
    """
    Create a pixel art sprite from an image file using half-block characters.

    Uses the lower half block character (▄) with foreground and background colors
    to display 2 vertical pixels per character cell, creating near-square pixels.

    Args:
        image_path: Path to the image file (PNG, JPG, etc.)
        width: Target width in pixels
        height: Target height in pixels (should be even for best results)
        x: Sprite x position in cells (default 0)
        y: Sprite y position in cells (default 0)
        mode: Downscaling algorithm - "average" (box filter) or "mode" (most frequent color)
        transparency_threshold: Alpha values below this are considered transparent (0-255)
        z_index: Drawing order (higher = on top)
        blocks_light: Whether sprite casts shadows
        emissive: Whether sprite glows (bypasses bloom threshold)
        lerp_speed: Movement interpolation speed in cells/sec (0 = instant)

    Returns:
        A Sprite object that can be added to a window

    Example:
        sprite = pyunicodegame.create_sprite_from_image(
            "character.png",
            width=32,
            height=32,
            mode="average",
        )
        window.add_sprite(sprite)

    Note:
        Requires Pillow (PIL). Install with: pip install Pillow
    """
    try:
        from PIL import Image
    except ImportError:
        raise ImportError(
            "Pillow is required for create_sprite_from_image. "
            "Install with: pip install Pillow"
        )

    from collections import Counter

    # Load and convert to RGBA
    img = Image.open(image_path).convert("RGBA")
    orig_width, orig_height = img.size

    if mode == "average":
        # BOX resampling does area averaging (box filter)
        img = img.resize((width, height), Image.Resampling.BOX)
    elif mode == "mode":
        # For mode, we need to manually compute most frequent color per block
        block_w = orig_width / width
        block_h = orig_height / height
        new_img = Image.new("RGBA", (width, height))

        for out_y in range(height):
            for out_x in range(width):
                # Get all pixels in this block
                x0 = int(out_x * block_w)
                y0 = int(out_y * block_h)
                x1 = int((out_x + 1) * block_w)
                y1 = int((out_y + 1) * block_h)

                pixels = []
                for py in range(y0, min(y1, orig_height)):
                    for px in range(x0, min(x1, orig_width)):
                        pixels.append(img.getpixel((px, py)))

                if pixels:
                    # Find most frequent color
                    most_common = Counter(pixels).most_common(1)[0][0]
                    new_img.putpixel((out_x, out_y), most_common)

        img = new_img
    else:
        raise ValueError(f"mode must be 'average' or 'mode', got '{mode}'")

    # Build character and color grids
    # Height in character rows = pixel height / 2 (ceiling division)
    char_height = (height + 1) // 2

    chars: List[List[str]] = []
    fg_colors: List[List[Optional[Tuple[int, int, int]]]] = []
    bg_colors: List[List[Optional[Tuple[int, int, int, int]]]] = []

    for char_row in range(char_height):
        chars.append([])
        fg_colors.append([])
        bg_colors.append([])

        top_y = char_row * 2
        bot_y = char_row * 2 + 1

        for col in range(width):
            top_pixel = img.getpixel((col, top_y))
            # Handle odd height - bottom pixel may not exist
            if bot_y < height:
                bot_pixel = img.getpixel((col, bot_y))
            else:
                bot_pixel = (0, 0, 0, 0)

            top_transparent = top_pixel[3] < transparency_threshold
            bot_transparent = bot_pixel[3] < transparency_threshold

            if top_transparent and bot_transparent:
                # Both transparent - use space
                chars[char_row].append(' ')
                fg_colors[char_row].append(None)
                bg_colors[char_row].append(None)
            else:
                # Use lower half block: fg = bottom pixel, bg = top pixel
                chars[char_row].append('\u2584')  # ▄
                fg_colors[char_row].append((bot_pixel[0], bot_pixel[1], bot_pixel[2]))
                bg_colors[char_row].append((top_pixel[0], top_pixel[1], top_pixel[2], 255))

    frame = SpriteFrame(chars, fg_colors, bg_colors)
    sprite = Sprite([frame], (255, 255, 255), None)
    sprite.x = x
    sprite.y = y
    sprite._teleport_pending = True
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
    follow_sprite: Optional[Sprite] = None,
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
    font_name: str = DEFAULT_FONT,
) -> Window:
    """
    Initialize pyunicodegame and pygame, creating a window sized for unicode cells.

    Cell size depends on the root font: 5x8, 6x13, 9x18, or 10x20 pixels.
    So width=80, height=25 with 10x20 font creates an 800x500 pixel window.

    A root window is automatically created that fills the screen.

    Args:
        title: Window title displayed in the title bar
        width: Grid width in unicode cells (default 80)
        height: Grid height in unicode cells (default 25)
        bg: Root window background color (R, G, B, A), default transparent
        font_name: Font for the root window - "5x8", "6x13", "9x18", "10x20" (default),
            or "unifontex" (8x16, duospace with full Unicode/CJK support).
            Also determines the base cell size and pygame window dimensions.

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
    _load_font(font_name)
    _root_cell_width, _root_cell_height = _font_dimensions[font_name]

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
    root = create_window("root", 0, 0, width, height, z_index=0, font_name=font_name, bg=bg)
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
) -> Window:
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


def get_window(name: str) -> Window:
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
    on_event: Optional[Callable[[pygame.event.Event], bool]] = None,
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
        on_key: Called when a key is pressed, with the pygame key code.
        on_event: Called for every pygame event. Return True to consume the event
                  (prevents default handling like Escape to quit). Receives the
                  full pygame.event.Event object for maximum flexibility.

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

        # With full event handling
        def on_event(event):
            if event.type == pygame.MOUSEMOTION:
                print(f"Mouse at {event.pos}")
            elif event.type == pygame.TEXTINPUT:
                print(f"Typed: {event.text}")
            return False  # Let default handling proceed

        pyunicodegame.run(on_event=on_event)
    """
    global _running, _fullscreen

    _running = True
    while _running:
        dt = _clock.tick(60) / 1000.0

        for event in pygame.event.get():
            # Let on_event handle the event first
            consumed = False
            if on_event:
                consumed = on_event(event)

            if consumed:
                continue

            # Default event handling
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
                apply_bloom(
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
            else:
                # Depth affects parallax (depth=0 moves 1:1, higher = slower)
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
    depth_scale: float = None,
) -> None:
    """
    Configure the global camera.

    Windows with higher depth values move slower (parallax effect).
    depth=0 moves 1:1 with camera, higher values move slower.

    Args:
        x: Camera X position in pixels (None = unchanged)
        y: Camera Y position in pixels (None = unchanged)
        depth_scale: How much depth affects parallax (default 0.1, None = unchanged)

    Example:
        # Set parallax intensity
        pyunicodegame.set_camera(depth_scale=0.1)

        # Move camera to position
        pyunicodegame.set_camera(x=100, y=50)
    """
    global _camera_x, _camera_y, _camera_depth_scale
    if x is not None:
        _camera_x = x
    if y is not None:
        _camera_y = y
    if depth_scale is not None:
        _camera_depth_scale = depth_scale


def get_camera() -> Tuple[float, float, float]:
    """
    Get the current camera state.

    Returns:
        Tuple of (x, y, depth_scale)
    """
    return (_camera_x, _camera_y, _camera_depth_scale)


def move_camera(dx: float, dy: float) -> None:
    """
    Move the camera by a relative amount.

    Args:
        dx: X offset in pixels
        dy: Y offset in pixels
    """
    global _camera_x, _camera_y
    _camera_x += dx
    _camera_y += dy
