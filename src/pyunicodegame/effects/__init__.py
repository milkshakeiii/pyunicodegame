"""
pyunicodegame.effects - Visual effects for TUI graphics.

This module provides visual effects including:
- Animation: Property tweening with easing functions
- Particles: Text-based particle systems for explosions, sparks, etc.
- Bloom: Glow/bloom post-processing effects
"""

from .animation import Animation, FrameAnimation, ease_linear, ease_in_quad, ease_out_quad, ease_in_out_quad
from .particles import Particle, ParticleConfig, ParticleEmitter, ParticleSystem, explosion, sparks, smoke, trail

__all__ = [
    "Animation",
    "FrameAnimation",
    "ease_linear",
    "ease_in_quad",
    "ease_out_quad",
    "ease_in_out_quad",
    "Particle",
    "ParticleConfig",
    "ParticleEmitter",
    "ParticleSystem",
    "explosion",
    "sparks",
    "smoke",
    "trail",
]
