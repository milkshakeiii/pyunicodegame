"""
pyunicodegame.effects.particles - Text-based particle systems.

QUICK START:
    from pyunicodegame.effects import explosion, sparks, ParticleSystem

    # Spawn an explosion
    renderer.spawn_particles(explosion(10, 5))

    # Custom particle system
    system = ParticleSystem(x=10, y=5)
    system.burst(count=20, config=ParticleConfig(chars="*+."))

CLASSES:
    Particle: Single particle data
    ParticleConfig: Configuration for particle behavior
    ParticleEmitter: Continuous particle spawner
    ParticleSystem: Collection of particles with physics

FACTORY FUNCTIONS:
    explosion(x, y) - Burst of particles in all directions
    sparks(x, y, direction) - Directional sparks
    smoke(x, y) - Rising smoke particles
    trail(x, y, dx, dy) - Movement trail
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple
import random
import math

from ..core.colors import Color


@dataclass
class Particle:
    """
    A single particle with physics properties.

    Attributes:
        x, y: Position in grid coordinates (float for smooth movement)
        char: Character to render
        color: RGB color tuple
        velocity: (vx, vy) velocity vector
        lifetime: Total lifetime in seconds
        age: Current age in seconds
        glow: Glow intensity (0.0 to 1.0)
        gravity: Downward acceleration
        friction: Velocity damping (1.0 = no friction, 0.0 = stops instantly)
        fade: Whether to fade out over lifetime
    """
    x: float
    y: float
    char: str
    color: Color
    velocity: Tuple[float, float] = (0.0, 0.0)
    lifetime: float = 1.0
    age: float = 0.0
    glow: float = 0.0
    gravity: float = 0.0
    friction: float = 1.0
    fade: bool = True

    @property
    def is_alive(self) -> bool:
        """Check if the particle is still active."""
        return self.age < self.lifetime

    @property
    def alpha(self) -> float:
        """Get the current alpha based on age and fade setting."""
        if not self.fade or self.lifetime <= 0:
            return 1.0
        return max(0.0, 1.0 - (self.age / self.lifetime))


@dataclass
class ParticleConfig:
    """
    Configuration for particle generation.

    Attributes:
        chars: Characters to randomly select from
        colors: Colors to randomly select from (None = white)
        velocity_range: (min, max) for random velocity components
        lifetime_range: (min, max) for particle lifetime
        gravity: Downward acceleration
        friction: Velocity damping factor
        glow: Base glow intensity
        glow_range: (min, max) for random glow variation
        fade: Whether particles fade over lifetime
    """
    chars: str = "*+."
    colors: Optional[List[Color]] = None
    velocity_range: Tuple[float, float] = (-3.0, 3.0)
    lifetime_range: Tuple[float, float] = (0.5, 1.5)
    gravity: float = 0.0
    friction: float = 0.98
    glow: float = 0.3
    glow_range: Tuple[float, float] = (0.0, 0.0)
    fade: bool = True

    def create_particle(
        self,
        x: float,
        y: float,
        direction: Optional[Tuple[float, float]] = None,
        speed_multiplier: float = 1.0,
    ) -> Particle:
        """
        Create a particle with randomized properties.

        Args:
            x, y: Spawn position
            direction: Optional direction vector (normalized)
            speed_multiplier: Velocity multiplier

        Returns:
            A new Particle instance
        """
        # Random character
        char = random.choice(self.chars)

        # Random color
        if self.colors:
            color = random.choice(self.colors)
        else:
            color = (255, 255, 255)

        # Random velocity
        if direction:
            # Velocity in specified direction with some randomness
            base_speed = random.uniform(*self.velocity_range) * speed_multiplier
            vx = direction[0] * abs(base_speed) + random.uniform(-0.5, 0.5)
            vy = direction[1] * abs(base_speed) + random.uniform(-0.5, 0.5)
        else:
            # Random omnidirectional velocity
            vx = random.uniform(*self.velocity_range) * speed_multiplier
            vy = random.uniform(*self.velocity_range) * speed_multiplier

        # Random lifetime
        lifetime = random.uniform(*self.lifetime_range)

        # Random glow
        glow = self.glow
        if self.glow_range[0] != self.glow_range[1]:
            glow += random.uniform(*self.glow_range)
        glow = max(0.0, min(1.0, glow))

        return Particle(
            x=x,
            y=y,
            char=char,
            color=color,
            velocity=(vx, vy),
            lifetime=lifetime,
            age=0.0,
            glow=glow,
            gravity=self.gravity,
            friction=self.friction,
            fade=self.fade,
        )


@dataclass
class ParticleEmitter:
    """
    Continuously spawns particles at a rate.

    Attributes:
        config: Particle configuration
        spawn_rate: Particles per second
        max_particles: Maximum concurrent particles
        spread: (x, y) random offset for spawn position
        direction: Optional emission direction
        active: Whether the emitter is spawning
    """
    config: ParticleConfig = field(default_factory=ParticleConfig)
    spawn_rate: float = 10.0
    max_particles: int = 100
    spread: Tuple[float, float] = (0.0, 0.0)
    direction: Optional[Tuple[float, float]] = None
    active: bool = True

    _spawn_accumulator: float = field(default=0.0, init=False)

    def update(
        self,
        dt: float,
        origin: Tuple[float, float],
        current_count: int,
    ) -> List[Particle]:
        """
        Update the emitter and spawn new particles.

        Args:
            dt: Time since last update in seconds
            origin: Current spawn position
            current_count: Number of existing particles

        Returns:
            List of newly spawned particles
        """
        if not self.active:
            return []

        new_particles = []
        self._spawn_accumulator += dt * self.spawn_rate

        while self._spawn_accumulator >= 1.0 and current_count + len(new_particles) < self.max_particles:
            self._spawn_accumulator -= 1.0

            # Apply spread
            x = origin[0] + random.uniform(-self.spread[0], self.spread[0])
            y = origin[1] + random.uniform(-self.spread[1], self.spread[1])

            new_particles.append(
                self.config.create_particle(x, y, self.direction)
            )

        return new_particles


class ParticleSystem:
    """
    A collection of particles with physics simulation.

    Manages particle lifecycle, physics updates, and provides
    convenient methods for creating common effects.

    Attributes:
        x, y: System origin position
        particles: List of active particles
        emitter: Optional continuous emitter
    """

    def __init__(
        self,
        x: float,
        y: float,
        emitter: Optional[ParticleEmitter] = None,
    ):
        """
        Initialize a particle system.

        Args:
            x, y: Origin position
            emitter: Optional emitter for continuous spawning
        """
        self.x = x
        self.y = y
        self.particles: List[Particle] = []
        self.emitter = emitter
        self._alive = True

    def burst(
        self,
        count: int,
        config: Optional[ParticleConfig] = None,
        direction: Optional[Tuple[float, float]] = None,
        speed_multiplier: float = 1.0,
    ) -> None:
        """
        Spawn a burst of particles immediately.

        Args:
            count: Number of particles to spawn
            config: Particle configuration (default if None)
            direction: Optional emission direction
            speed_multiplier: Velocity multiplier
        """
        if config is None:
            config = ParticleConfig()

        for _ in range(count):
            self.particles.append(
                config.create_particle(self.x, self.y, direction, speed_multiplier)
            )

    def update(self, dt: float) -> None:
        """
        Update all particles and spawn new ones from emitter.

        Args:
            dt: Time since last update in seconds
        """
        # Spawn from emitter
        if self.emitter:
            new_particles = self.emitter.update(
                dt,
                (self.x, self.y),
                len(self.particles)
            )
            self.particles.extend(new_particles)

        # Update existing particles
        alive_particles = []
        for p in self.particles:
            p.age += dt

            if p.is_alive:
                # Apply physics
                vx, vy = p.velocity
                vy += p.gravity * dt
                vx *= p.friction
                vy *= p.friction
                p.velocity = (vx, vy)

                p.x += vx * dt
                p.y += vy * dt

                alive_particles.append(p)

        self.particles = alive_particles

        # Check if system is dead
        if not self.particles and (not self.emitter or not self.emitter.active):
            self._alive = False

    def is_alive(self) -> bool:
        """Check if the system has any active particles or emitter."""
        return self._alive

    def get_particles(self) -> List[Particle]:
        """Get all active particles."""
        return self.particles

    def move_to(self, x: float, y: float) -> None:
        """Move the system origin."""
        self.x = x
        self.y = y

    def stop_emitting(self) -> None:
        """Stop the emitter from spawning new particles."""
        if self.emitter:
            self.emitter.active = False

    def clear(self) -> None:
        """Remove all particles."""
        self.particles.clear()


# -----------------------------------------------------------------------------
# Factory Functions
# -----------------------------------------------------------------------------

def explosion(
    x: float,
    y: float,
    intensity: float = 1.0,
    colors: Optional[List[Color]] = None,
) -> ParticleSystem:
    """
    Create an explosion particle burst.

    Args:
        x, y: Center position
        intensity: Size/power multiplier
        colors: Custom color palette (default = fire colors)

    Returns:
        A ParticleSystem with explosion particles
    """
    if colors is None:
        colors = [
            (255, 255, 100),  # Bright yellow
            (255, 200, 50),   # Orange-yellow
            (255, 150, 0),    # Orange
            (255, 100, 0),    # Red-orange
            (255, 50, 0),     # Red
        ]

    config = ParticleConfig(
        chars="*+#@%&",
        colors=colors,
        velocity_range=(-5.0 * intensity, 5.0 * intensity),
        lifetime_range=(0.3, 1.0),
        gravity=3.0,
        friction=0.95,
        glow=0.8,
        fade=True,
    )

    system = ParticleSystem(x, y)
    system.burst(int(20 * intensity), config)
    return system


def sparks(
    x: float,
    y: float,
    direction: Tuple[float, float] = (0.0, -1.0),
    intensity: float = 1.0,
    color: Optional[Color] = None,
) -> ParticleSystem:
    """
    Create directional sparks.

    Args:
        x, y: Origin position
        direction: Emission direction (normalized)
        intensity: Size/power multiplier
        color: Spark color (default = yellow)

    Returns:
        A ParticleSystem with spark particles
    """
    if color is None:
        color = (255, 200, 50)

    colors = [
        color,
        (min(255, color[0] + 50), min(255, color[1] + 50), min(255, color[2])),
    ]

    config = ParticleConfig(
        chars=".*+",
        colors=colors,
        velocity_range=(2.0 * intensity, 6.0 * intensity),
        lifetime_range=(0.2, 0.6),
        gravity=5.0,
        friction=0.9,
        glow=0.6,
        fade=True,
    )

    # Normalize direction
    mag = math.sqrt(direction[0] ** 2 + direction[1] ** 2)
    if mag > 0:
        direction = (direction[0] / mag, direction[1] / mag)

    system = ParticleSystem(x, y)
    system.burst(int(15 * intensity), config, direction, 1.0)
    return system


def smoke(
    x: float,
    y: float,
    intensity: float = 1.0,
    duration: float = 2.0,
) -> ParticleSystem:
    """
    Create rising smoke particles.

    Args:
        x, y: Origin position
        intensity: Density multiplier
        duration: How long to emit (0 = burst only)

    Returns:
        A ParticleSystem with smoke particles
    """
    colors = [
        (80, 80, 80),
        (100, 100, 100),
        (120, 120, 120),
        (140, 140, 140),
    ]

    config = ParticleConfig(
        chars=".oO",
        colors=colors,
        velocity_range=(-0.5, 0.5),
        lifetime_range=(1.0, 2.5),
        gravity=-1.5,  # Rise up
        friction=0.98,
        glow=0.0,
        fade=True,
    )

    if duration > 0:
        emitter = ParticleEmitter(
            config=config,
            spawn_rate=10.0 * intensity,
            max_particles=50,
            spread=(0.5, 0.0),
        )
        system = ParticleSystem(x, y, emitter)
    else:
        system = ParticleSystem(x, y)
        system.burst(int(10 * intensity), config)

    return system


def trail(
    x: float,
    y: float,
    vx: float,
    vy: float,
    color: Optional[Color] = None,
) -> ParticleSystem:
    """
    Create a movement trail effect.

    Args:
        x, y: Current position
        vx, vy: Movement velocity (trail goes opposite direction)
        color: Trail color (default = white)

    Returns:
        A ParticleSystem for trailing particles
    """
    if color is None:
        color = (200, 200, 255)

    config = ParticleConfig(
        chars=".",
        colors=[color],
        velocity_range=(-0.5, 0.5),
        lifetime_range=(0.2, 0.5),
        gravity=0.0,
        friction=0.8,
        glow=0.3,
        fade=True,
    )

    # Trail opposite to movement
    direction = (-vx, -vy)
    mag = math.sqrt(direction[0] ** 2 + direction[1] ** 2)
    if mag > 0:
        direction = (direction[0] / mag, direction[1] / mag)

    emitter = ParticleEmitter(
        config=config,
        spawn_rate=20.0,
        max_particles=30,
        direction=direction,
    )

    return ParticleSystem(x, y, emitter)


def blood_splatter(
    x: float,
    y: float,
    direction: Tuple[float, float] = (1.0, 0.0),
    intensity: float = 1.0,
) -> ParticleSystem:
    """
    Create a blood/damage splatter effect.

    Args:
        x, y: Impact position
        direction: Splatter direction
        intensity: Size multiplier

    Returns:
        A ParticleSystem with blood particles
    """
    colors = [
        (180, 0, 0),
        (150, 0, 0),
        (120, 0, 0),
        (200, 20, 20),
    ]

    config = ParticleConfig(
        chars="*.,;:'",
        colors=colors,
        velocity_range=(2.0 * intensity, 5.0 * intensity),
        lifetime_range=(0.5, 1.5),
        gravity=8.0,
        friction=0.85,
        glow=0.0,
        fade=True,
    )

    # Normalize direction
    mag = math.sqrt(direction[0] ** 2 + direction[1] ** 2)
    if mag > 0:
        direction = (direction[0] / mag, direction[1] / mag)

    system = ParticleSystem(x, y)
    system.burst(int(15 * intensity), config, direction, 1.0)
    return system


def magic_sparkle(
    x: float,
    y: float,
    color: Color = (100, 150, 255),
    intensity: float = 1.0,
) -> ParticleSystem:
    """
    Create magical sparkle particles.

    Args:
        x, y: Center position
        color: Base sparkle color
        intensity: Density multiplier

    Returns:
        A ParticleSystem with sparkle particles
    """
    # Create color variations
    colors = [
        color,
        (min(255, color[0] + 50), min(255, color[1] + 50), min(255, color[2] + 50)),
        (255, 255, 255),
    ]

    config = ParticleConfig(
        chars="*+.",
        colors=colors,
        velocity_range=(-1.5 * intensity, 1.5 * intensity),
        lifetime_range=(0.3, 0.8),
        gravity=-2.0,
        friction=0.95,
        glow=0.9,
        glow_range=(-0.2, 0.2),
        fade=True,
    )

    system = ParticleSystem(x, y)
    system.burst(int(12 * intensity), config)
    return system
