"""
pyunicodegame.layers - Layer management for compositing.

This module provides layer-based rendering:
- Layer: A single rendering layer with visibility and alpha
- LayerStack: Z-ordered management of multiple layers
"""

from .layer import Layer
from .layer_stack import LayerStack

__all__ = [
    "Layer",
    "LayerStack",
]
