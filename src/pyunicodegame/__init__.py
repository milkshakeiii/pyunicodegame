"""
pyunicodegame - A Cogmind-inspired pygame library for TUI-style graphics.

This library provides tools for creating text-based graphics with modern
effects like glow/bloom and particle systems, all rendered through pygame.

QUICK START:
    import pygame
    import pyunicodegame

    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    clock = pygame.time.Clock()

    # Create renderer with 80x25 grid, scaled 2x
    renderer = pyunicodegame.Renderer(width=80, height=25, scale=2)

    running = True
    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Clear and draw
        renderer.clear()
        renderer.put(10, 5, "@", fg=(0, 255, 0), glow=0.5)
        renderer.put_string(0, 0, "Hello, World!")
        renderer.draw_panel(20, 2, 30, 10, title="Status")

        # Update animations/particles and render
        renderer.update(dt)
        renderer.render(screen)

        pygame.display.flip()

MAIN CLASSES:
    Renderer     - Main interface for all rendering operations
    Grid         - 2D buffer of cells for text content
    Cell         - Single cell with character, colors, and glow
    GlyphCache   - Efficient caching of rendered character sprites

UI COMPONENTS:
    Panel        - Bordered window/panel with optional title
    BorderStyle  - Box-drawing character configurations

EFFECTS:
    Animation       - Property tweening with easing functions
    FrameAnimation  - Frame-based character animation
    ParticleSystem  - Text-based particle effects
    explosion()     - Create an explosion particle burst
    sparks()        - Create directional sparks
    smoke()         - Create rising smoke
    BloomProcessor  - Glow/bloom post-processing

THEMING:
    Theme           - Base theme configuration
    CogmindTheme    - Cogmind-inspired color palette

For detailed documentation, see the individual module docstrings
or the README.md file.
"""

__version__ = "0.1.0"

# Core classes
from .core.renderer import Renderer
from .core.grid import Grid, Cell
from .core.glyph_cache import GlyphCache
from .core.colors import (
    Color,
    lerp_color,
    brighten,
    darken,
    multiply_color,
    add_colors,
    BLACK,
    WHITE,
    RED,
    GREEN,
    BLUE,
    YELLOW,
    CYAN,
    MAGENTA,
    ORANGE,
    GRAY,
)
from .core.fonts import get_default_font_path, load_font

# UI components
from .ui.borders import BorderStyle
from .ui.panel import Panel
from .ui.text import wrap_text, align_text, truncate

# Layers
from .layers.layer import Layer
from .layers.layer_stack import LayerStack

# Effects
from .effects.animation import (
    Animation,
    FrameAnimation,
    ease_linear,
    ease_in_quad,
    ease_out_quad,
    ease_in_out_quad,
    ease_in_cubic,
    ease_out_cubic,
    ease_in_out_cubic,
    ease_in_sine,
    ease_out_sine,
    ease_out_bounce,
    ease_out_elastic,
)
from .effects.particles import (
    Particle,
    ParticleConfig,
    ParticleEmitter,
    ParticleSystem,
    explosion,
    sparks,
    smoke,
    trail,
    blood_splatter,
    magic_sparkle,
)
from .effects.bloom import BloomProcessor, BloomQuality

# Themes
from .themes.theme import Theme, DARK_THEME, LIGHT_THEME, RETRO_GREEN_THEME, AMBER_THEME
from .themes.cogmind import CogmindTheme, CogmindBrightTheme, CogmindWarmTheme, CogmindMinimalTheme

__all__ = [
    # Version
    "__version__",

    # Core
    "Renderer",
    "Grid",
    "Cell",
    "GlyphCache",
    "Color",
    "lerp_color",
    "brighten",
    "darken",
    "multiply_color",
    "add_colors",
    "get_default_font_path",
    "load_font",

    # Color constants
    "BLACK",
    "WHITE",
    "RED",
    "GREEN",
    "BLUE",
    "YELLOW",
    "CYAN",
    "MAGENTA",
    "ORANGE",
    "GRAY",

    # UI
    "BorderStyle",
    "Panel",
    "wrap_text",
    "align_text",
    "truncate",

    # Layers
    "Layer",
    "LayerStack",

    # Effects - Animation
    "Animation",
    "FrameAnimation",
    "ease_linear",
    "ease_in_quad",
    "ease_out_quad",
    "ease_in_out_quad",
    "ease_in_cubic",
    "ease_out_cubic",
    "ease_in_out_cubic",
    "ease_in_sine",
    "ease_out_sine",
    "ease_out_bounce",
    "ease_out_elastic",

    # Effects - Particles
    "Particle",
    "ParticleConfig",
    "ParticleEmitter",
    "ParticleSystem",
    "explosion",
    "sparks",
    "smoke",
    "trail",
    "blood_splatter",
    "magic_sparkle",

    # Effects - Bloom
    "BloomProcessor",
    "BloomQuality",

    # Themes
    "Theme",
    "CogmindTheme",
    "CogmindBrightTheme",
    "CogmindWarmTheme",
    "CogmindMinimalTheme",
    "DARK_THEME",
    "LIGHT_THEME",
    "RETRO_GREEN_THEME",
    "AMBER_THEME",
]
