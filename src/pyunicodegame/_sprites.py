"""Sprite classes for pyunicodegame."""

from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from . import Window


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

    def add_animation(self, animation: Animation) -> None:
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

    def draw(self, window: Window) -> None:
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

    def draw(self, window: Window) -> None:
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

    def update(self, dt: float, window: Window) -> None:
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

    def _spawn_particle(self, window: Window) -> None:
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
