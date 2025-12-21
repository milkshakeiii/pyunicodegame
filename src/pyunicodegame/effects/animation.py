"""
pyunicodegame.effects.animation - Animation and easing functions.

QUICK START:
    from pyunicodegame.effects import Animation, ease_out_quad

    # Animate a property
    anim = Animation(
        duration=1.0,
        start_value=0.0,
        end_value=1.0,
        easing=ease_out_quad,
        on_update=lambda v: print(f"Value: {v}")
    )

    # Frame animation for character cycling
    spinner = FrameAnimation(frames=["|", "/", "-", "\\\\"], fps=8)

CLASSES:
    Animation: Property tweening with easing
    FrameAnimation: Frame-based character animation

FUNCTIONS:
    ease_linear, ease_in_quad, ease_out_quad, ease_in_out_quad, etc.
"""

from dataclasses import dataclass, field
from typing import Callable, List, Optional, Any, TypeVar, Union
import math

# Type for values that can be animated (numbers or tuples of numbers)
T = TypeVar('T', float, int, tuple)

# Easing function type
EasingFunc = Callable[[float], float]


# -----------------------------------------------------------------------------
# Easing Functions
# -----------------------------------------------------------------------------

def ease_linear(t: float) -> float:
    """Linear interpolation (no easing)."""
    return t


def ease_in_quad(t: float) -> float:
    """Quadratic ease-in (slow start)."""
    return t * t


def ease_out_quad(t: float) -> float:
    """Quadratic ease-out (slow end)."""
    return 1 - (1 - t) * (1 - t)


def ease_in_out_quad(t: float) -> float:
    """Quadratic ease-in-out (slow start and end)."""
    if t < 0.5:
        return 2 * t * t
    else:
        return 1 - (-2 * t + 2) ** 2 / 2


def ease_in_cubic(t: float) -> float:
    """Cubic ease-in."""
    return t ** 3


def ease_out_cubic(t: float) -> float:
    """Cubic ease-out."""
    return 1 - (1 - t) ** 3


def ease_in_out_cubic(t: float) -> float:
    """Cubic ease-in-out."""
    if t < 0.5:
        return 4 * t ** 3
    else:
        return 1 - (-2 * t + 2) ** 3 / 2


def ease_in_sine(t: float) -> float:
    """Sinusoidal ease-in."""
    return 1 - math.cos((t * math.pi) / 2)


def ease_out_sine(t: float) -> float:
    """Sinusoidal ease-out."""
    return math.sin((t * math.pi) / 2)


def ease_in_out_sine(t: float) -> float:
    """Sinusoidal ease-in-out."""
    return -(math.cos(math.pi * t) - 1) / 2


def ease_in_expo(t: float) -> float:
    """Exponential ease-in."""
    return 0 if t == 0 else 2 ** (10 * t - 10)


def ease_out_expo(t: float) -> float:
    """Exponential ease-out."""
    return 1 if t == 1 else 1 - 2 ** (-10 * t)


def ease_in_elastic(t: float) -> float:
    """Elastic ease-in (overshoot with bounce)."""
    if t == 0 or t == 1:
        return t
    c4 = (2 * math.pi) / 3
    return -2 ** (10 * t - 10) * math.sin((t * 10 - 10.75) * c4)


def ease_out_elastic(t: float) -> float:
    """Elastic ease-out (overshoot with bounce)."""
    if t == 0 or t == 1:
        return t
    c4 = (2 * math.pi) / 3
    return 2 ** (-10 * t) * math.sin((t * 10 - 0.75) * c4) + 1


def ease_out_bounce(t: float) -> float:
    """Bounce ease-out."""
    n1 = 7.5625
    d1 = 2.75

    if t < 1 / d1:
        return n1 * t * t
    elif t < 2 / d1:
        t -= 1.5 / d1
        return n1 * t * t + 0.75
    elif t < 2.5 / d1:
        t -= 2.25 / d1
        return n1 * t * t + 0.9375
    else:
        t -= 2.625 / d1
        return n1 * t * t + 0.984375


# -----------------------------------------------------------------------------
# Animation Classes
# -----------------------------------------------------------------------------

@dataclass
class Animation:
    """
    Animate a value over time with easing.

    The animation interpolates between start_value and end_value over
    the specified duration, applying an easing function.

    Attributes:
        duration: Animation duration in seconds
        start_value: Initial value
        end_value: Final value
        easing: Easing function to apply
        on_update: Callback called with current value each update
        on_complete: Callback called when animation finishes
        loop: Whether to loop the animation
        ping_pong: If looping, alternate direction
    """
    duration: float
    start_value: Union[float, tuple] = 0.0
    end_value: Union[float, tuple] = 1.0
    easing: EasingFunc = ease_linear
    on_update: Optional[Callable[[Any], None]] = None
    on_complete: Optional[Callable[[], None]] = None
    loop: bool = False
    ping_pong: bool = False

    # Internal state
    _elapsed: float = field(default=0.0, init=False)
    _complete: bool = field(default=False, init=False)
    _forward: bool = field(default=True, init=False)

    @property
    def progress(self) -> float:
        """Get the raw progress (0.0 to 1.0)."""
        if self.duration <= 0:
            return 1.0
        return min(1.0, self._elapsed / self.duration)

    @property
    def value(self) -> Any:
        """Get the current interpolated value."""
        t = self.easing(self.progress)
        if not self._forward:
            t = 1.0 - t
        return self._interpolate(t)

    @property
    def is_complete(self) -> bool:
        """Check if the animation has finished."""
        return self._complete

    def _interpolate(self, t: float) -> Any:
        """Interpolate between start and end values."""
        if isinstance(self.start_value, tuple):
            # Interpolate each component
            return tuple(
                self.start_value[i] + (self.end_value[i] - self.start_value[i]) * t
                for i in range(len(self.start_value))
            )
        else:
            return self.start_value + (self.end_value - self.start_value) * t

    def update(self, dt: float) -> bool:
        """
        Update the animation.

        Args:
            dt: Time since last update in seconds

        Returns:
            True if the animation is still active, False if complete
        """
        if self._complete:
            return False

        self._elapsed += dt

        # Check for completion
        if self._elapsed >= self.duration:
            if self.loop:
                if self.ping_pong:
                    self._forward = not self._forward
                self._elapsed = self._elapsed % self.duration
            else:
                self._elapsed = self.duration
                self._complete = True

        # Call update callback
        if self.on_update:
            self.on_update(self.value)

        # Call complete callback
        if self._complete and self.on_complete:
            self.on_complete()

        return not self._complete

    def reset(self) -> None:
        """Reset the animation to the beginning."""
        self._elapsed = 0.0
        self._complete = False
        self._forward = True


@dataclass
class FrameAnimation:
    """
    Frame-based animation for cycling through characters.

    Useful for animated sprites that cycle through a sequence
    of characters at a fixed rate.

    Attributes:
        frames: List of characters/strings to cycle through
        fps: Frames per second
        loop: Whether to loop when finished
    """
    frames: List[str]
    fps: float = 10.0
    loop: bool = True

    # Internal state
    _time: float = field(default=0.0, init=False)
    _frame_index: int = field(default=0, init=False)
    _complete: bool = field(default=False, init=False)

    @property
    def frame_duration(self) -> float:
        """Duration of each frame in seconds."""
        return 1.0 / self.fps if self.fps > 0 else 1.0

    @property
    def current_frame(self) -> str:
        """Get the current frame character."""
        if not self.frames:
            return " "
        return self.frames[self._frame_index % len(self.frames)]

    @property
    def frame_index(self) -> int:
        """Get the current frame index."""
        return self._frame_index

    @property
    def is_complete(self) -> bool:
        """Check if a non-looping animation has finished."""
        return self._complete

    def update(self, dt: float) -> bool:
        """
        Update the frame animation.

        Args:
            dt: Time since last update in seconds

        Returns:
            True if the animation is still active
        """
        if self._complete:
            return False

        self._time += dt

        # Calculate new frame
        while self._time >= self.frame_duration:
            self._time -= self.frame_duration
            self._frame_index += 1

            # Handle end of animation
            if self._frame_index >= len(self.frames):
                if self.loop:
                    self._frame_index = 0
                else:
                    self._frame_index = len(self.frames) - 1
                    self._complete = True
                    return False

        return True

    def reset(self) -> None:
        """Reset to the first frame."""
        self._time = 0.0
        self._frame_index = 0
        self._complete = False

    def set_frame(self, index: int) -> None:
        """Set the current frame index."""
        self._frame_index = index % len(self.frames) if self.frames else 0
        self._time = 0.0


# -----------------------------------------------------------------------------
# Animation Utilities
# -----------------------------------------------------------------------------

def chain_animations(*animations: Animation) -> Animation:
    """
    Create an animation that plays multiple animations in sequence.

    Note: This is a simple implementation that returns a wrapper.
    For complex chains, consider using a more sophisticated system.
    """
    total_duration = sum(a.duration for a in animations)

    def get_value_at_time(elapsed: float) -> Any:
        t = 0.0
        for anim in animations:
            if elapsed < t + anim.duration:
                anim._elapsed = elapsed - t
                return anim.value
            t += anim.duration
        return animations[-1].end_value if animations else 0.0

    # Create wrapper animation
    result = Animation(duration=total_duration)
    result._get_value = get_value_at_time
    return result
