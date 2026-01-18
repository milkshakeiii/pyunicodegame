#!/usr/bin/env python3
"""
Demo of the PixelSprite system.

Demonstrates:
- Creating pixel sprites programmatically (without image files)
- Grid alignment (pixel sprites align with unicode character grid)
- Animation using the shared Animation class
- PixelEffectSprite with velocity and fade
- Lighting and bloom affecting pixel sprites

Use arrow keys to move the candle. Press SPACE to emit particles.
"""

import random

import pygame
import pyunicodegame


def create_candle_frames(cell_w: int, cell_h: int) -> list:
    """Create candle sprite frames with flickering flame animation."""
    frames = []
    body_top = cell_h // 2

    # Frame variations for flame flicker
    flame_sizes = [
        (2, 4, 6),   # normal
        (2, 3, 5),   # smaller
        (3, 5, 7),   # larger
        (2, 4, 5),   # slightly smaller
    ]

    for outer_w, inner_w, height in flame_sizes:
        surf = pygame.Surface((cell_w, cell_h * 2), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 0))

        # Candle body (cream/white)
        pygame.draw.rect(surf, (240, 230, 200), (cell_w // 4, body_top, cell_w // 2, cell_h + cell_h // 2))

        # Wick
        wick_x = cell_w // 2
        pygame.draw.line(surf, (50, 40, 30), (wick_x, body_top - 2), (wick_x, body_top + 2), 1)

        # Flame (varies per frame)
        flame_cx = cell_w // 2
        flame_cy = body_top - 4
        pygame.draw.ellipse(surf, (255, 200, 50), (flame_cx - outer_w, flame_cy - height + 2, outer_w * 2, height))
        pygame.draw.ellipse(surf, (255, 255, 150), (flame_cx - 1, flame_cy - inner_w + 1, 2, inner_w))

        frames.append(surf)

    return frames


def create_pillar_sprite(cell_w: int, cell_h: int) -> pygame.Surface:
    """Create a stone pillar sprite (1x3 cells) that blocks light."""
    surf = pygame.Surface((cell_w, cell_h * 3), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 0))

    # Stone pillar with texture (brownish stone)
    pygame.draw.rect(surf, (140, 120, 100), (1, 0, cell_w - 2, cell_h * 3))

    # Add some stone texture lines
    for y in range(0, cell_h * 3, cell_h // 2):
        pygame.draw.line(surf, (100, 85, 70), (1, y), (cell_w - 2, y), 1)

    # Highlight on left edge
    pygame.draw.line(surf, (170, 150, 130), (1, 0), (1, cell_h * 3 - 1), 1)

    return surf


def create_particle_sprite(cell_w: int, cell_h: int, color: tuple) -> pygame.Surface:
    """Create a small particle sprite (1x1 cell)."""
    surf = pygame.Surface((cell_w, cell_h), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 0))
    # Draw a glowing dot
    cx, cy = cell_w // 2, cell_h // 2
    pygame.draw.circle(surf, (*color, 255), (cx, cy), min(cell_w, cell_h) // 3)
    pygame.draw.circle(surf, (255, 255, 255, 200), (cx, cy), min(cell_w, cell_h) // 6)
    return surf


def main():
    # Use unifont for 8x16 cell size
    root = pyunicodegame.init(
        "PixelSprite Demo",
        width=60,
        height=30,
        bg=(10, 10, 30, 255),
        font_name="unifont",
    )

    cell_w, cell_h = root.cell_size
    print(f"Cell size: {cell_w}x{cell_h} pixels")

    # Create candle with flickering flame animation
    candle_surfs = create_candle_frames(cell_w, cell_h)
    candle_frames = [
        pyunicodegame.PixelFrame(surf, cell_w, cell_h) for surf in candle_surfs
    ]

    candle = pyunicodegame.PixelSprite(candle_frames)
    candle.lerp_speed = 8
    candle.z_index = 10
    candle.move_to(30, 14, teleport=True)
    root.add_sprite(candle)

    # Add flickering flame animation
    flicker = pyunicodegame.create_animation(
        "flicker",
        [0, 1, 0, 2, 0, 3, 1, 2],
        frame_duration=0.1,
        loop=True,
    )
    candle.add_animation(flicker)
    candle.play_animation("flicker")

    # Create a stone pillar that blocks light
    pillar_surf = create_pillar_sprite(cell_w, cell_h)
    pillar_frame = pyunicodegame.PixelFrame(pillar_surf, cell_w, cell_h)
    pillar = pyunicodegame.PixelSprite([pillar_frame])
    pillar.blocks_light = True
    pillar.move_to(40, 12, teleport=True)
    root.add_sprite(pillar)

    # Add lighting - candle emits light, pillar casts shadow
    root.set_lighting(ambient=(30, 30, 50))
    candle_light = pyunicodegame.create_light(
        x=30,
        y=14,
        radius=25,
        color=(255, 180, 80),
        intensity=1.0,
        follow_sprite=candle,
    )
    root.add_light(candle_light)

    # Enable bloom
    root.set_bloom(enabled=True, threshold=200, intensity=1.5)

    # Particle frame for effects
    particle_surf = create_particle_sprite(cell_w, cell_h, (255, 200, 50))
    particle_frame = pyunicodegame.PixelFrame(particle_surf, cell_w, cell_h)

    def on_key(key):
        if key == pygame.K_LEFT:
            candle.move_to(candle.x - 1, candle.y)
        elif key == pygame.K_RIGHT:
            candle.move_to(candle.x + 1, candle.y)
        elif key == pygame.K_UP:
            candle.move_to(candle.x, candle.y - 1)
        elif key == pygame.K_DOWN:
            candle.move_to(candle.x, candle.y + 1)
        elif key == pygame.K_SPACE:
            # Emit pixel effect particles from flame
            for _ in range(5):
                effect = pyunicodegame.PixelEffectSprite([particle_frame])
                effect.x = float(candle.x)
                effect.y = float(candle.y) - 0.5
                effect.vx = random.uniform(-3, 3)
                effect.vy = random.uniform(-6, -2)
                effect.drag = 0.4
                effect.fade_time = 0.6
                effect.emissive = True
                effect.z_index = 5
                root.add_sprite(effect)
        elif key == pygame.K_q:
            pyunicodegame.quit()

    def render():
        # Draw ground line
        for x in range(root.width):
            root.put(x, 20, "═", (60, 40, 20))

        # Instructions
        root.put_string(1, 1, "PixelSprite Demo", (200, 200, 200))
        root.put_string(1, 2, "Arrow keys: move, SPACE: particles, Q: quit", (120, 120, 120))

        # Grid reference
        root.put_string(1, 28, f"Cell size: {cell_w}x{cell_h}px", (80, 80, 80))

    pyunicodegame.run(render=render, on_key=on_key)


if __name__ == "__main__":
    main()
