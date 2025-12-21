"""
pyunicodegame.layers.layer_stack - Z-ordered layer management.

QUICK START:
    from pyunicodegame.layers import LayerStack

    stack = LayerStack(width=80, height=25)
    stack.add_layer("background", z_index=0)
    stack.add_layer("entities", z_index=10)
    stack.add_layer("ui", z_index=100)

    # Draw to specific layers
    stack.get_layer("entities").put(10, 5, "@", (0, 255, 0))
    stack.get_layer("ui").put_string(0, 0, "HP: 100")

CLASSES:
    LayerStack: Z-ordered management of multiple layers
"""

from typing import Dict, List, Optional

from .layer import Layer
from ..core.colors import Color


class LayerStack:
    """
    Manages multiple layers with z-ordering.

    Layers are rendered in z_index order (lowest first, highest on top).
    The stack provides convenient access to layers by name.

    Attributes:
        width: Grid width for all layers
        height: Grid height for all layers
        layers: Dictionary of layer name to Layer
    """

    def __init__(self, width: int, height: int, default_bg: Optional[Color] = None):
        """
        Initialize the layer stack.

        Args:
            width: Grid width for all layers
            height: Grid height for all layers
            default_bg: Default background color for layers
        """
        self.width = width
        self.height = height
        self.default_bg = default_bg
        self._layers: Dict[str, Layer] = {}
        self._sorted_layers: List[Layer] = []
        self._needs_sort = False

    def add_layer(
        self,
        name: str,
        z_index: int = 0,
        visible: bool = True,
        alpha: float = 1.0,
    ) -> Layer:
        """
        Add a new layer to the stack.

        Args:
            name: Unique identifier for the layer
            z_index: Rendering order (higher = on top)
            visible: Whether the layer is visible
            alpha: Layer opacity

        Returns:
            The created Layer

        Raises:
            ValueError: If a layer with this name already exists
        """
        if name in self._layers:
            raise ValueError(f"Layer '{name}' already exists")

        layer = Layer(
            name=name,
            z_index=z_index,
            width=self.width,
            height=self.height,
            visible=visible,
            alpha=alpha,
            default_bg=self.default_bg,
        )

        self._layers[name] = layer
        self._needs_sort = True
        return layer

    def get_layer(self, name: str) -> Optional[Layer]:
        """
        Get a layer by name.

        Args:
            name: Layer identifier

        Returns:
            The Layer, or None if not found
        """
        return self._layers.get(name)

    def remove_layer(self, name: str) -> bool:
        """
        Remove a layer from the stack.

        Args:
            name: Layer identifier

        Returns:
            True if the layer was removed
        """
        if name in self._layers:
            del self._layers[name]
            self._needs_sort = True
            return True
        return False

    def set_z_index(self, name: str, z_index: int) -> bool:
        """
        Change a layer's z-index.

        Args:
            name: Layer identifier
            z_index: New z-index value

        Returns:
            True if the layer was found and updated
        """
        layer = self._layers.get(name)
        if layer:
            layer.z_index = z_index
            self._needs_sort = True
            return True
        return False

    def get_sorted_layers(self) -> List[Layer]:
        """
        Get all layers sorted by z-index.

        Returns:
            List of layers in render order (lowest z first)
        """
        if self._needs_sort:
            self._sorted_layers = sorted(
                self._layers.values(),
                key=lambda l: l.z_index
            )
            self._needs_sort = False
        return self._sorted_layers

    def get_visible_layers(self) -> List[Layer]:
        """
        Get all visible layers sorted by z-index.

        Returns:
            List of visible layers in render order
        """
        return [l for l in self.get_sorted_layers() if l.visible]

    def clear_all(self, bg: Optional[Color] = None) -> None:
        """Clear all layers."""
        for layer in self._layers.values():
            layer.clear(bg)

    def mark_all_dirty(self) -> None:
        """Mark all layers as needing re-render."""
        for layer in self._layers.values():
            layer.mark_dirty()

    def __contains__(self, name: str) -> bool:
        """Check if a layer exists."""
        return name in self._layers

    def __getitem__(self, name: str) -> Layer:
        """Get a layer by name (raises KeyError if not found)."""
        return self._layers[name]

    def __len__(self) -> int:
        """Get the number of layers."""
        return len(self._layers)

    def __iter__(self):
        """Iterate over layers in z-order."""
        return iter(self.get_sorted_layers())
