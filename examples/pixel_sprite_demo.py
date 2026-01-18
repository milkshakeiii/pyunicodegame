#!/usr/bin/env python3
"""
Demo of the PixelSprite system.

Demonstrates:
- Creating pixel sprites programmatically (without image files)
- Grid alignment (pixel sprites align with unicode character grid)
- Animation using the shared Animation class
- PixelEffectSprite with velocity and fade
- Mixing pixel sprites and unicode sprites in the same window
- Lighting and bloom affecting pixel sprites

Use arrow keys to move the pixel sprite. Press SPACE to emit particles.
"""

import pygame
import pyunicodegame


def create_test_image(width: int, height: int, color: tuple) -> pygame.Surface:
    """Create a simple test image with a colored rectangle and border."""
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    surface.fill((0, 0, 0, 0))

    # Draw filled rectangle with slight transparency
    pygame.draw.rect(surface, (*color, 200), (1, 1, width - 2, height - 2))

    # Draw border
    pygame.draw.rect(surface, (255, 255, 255, 255), (0, 0, width, height), 1)

    return surface


def create_character_sprite(cell_w: int, cell_h: int) -> list:
    """Create a simple character sprite (2x2 cells) with animation frames."""
    frames = []

    # Frame 0: Standing
    surf = pygame.Surface((cell_w * 2, cell_h * 2), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 0))
    # Head
    pygame.draw.circle(surf, (255, 220, 180), (cell_w, cell_h // 2 + 2), cell_w // 2)
    # Body
    pygame.draw.rect(surf, (0, 150, 255), (cell_w // 2, cell_h, cell_w, cell_h - 2))
    # Eyes
    pygame.draw.circle(surf, (0, 0, 0), (cell_w - 2, cell_h // 2), 1)
    pygame.draw.circle(surf, (0, 0, 0), (cell_w + 2, cell_h // 2), 1)
    frames.append(surf)

    # Frame 1: Walk left
    surf = pygame.Surface((cell_w * 2, cell_h * 2), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 0))
    pygame.draw.circle(surf, (255, 220, 180), (cell_w, cell_h // 2 + 2), cell_w // 2)
    pygame.draw.rect(surf, (0, 150, 255), (cell_w // 2, cell_h, cell_w, cell_h - 2))
    # Eyes looking left
    pygame.draw.circle(surf, (0, 0, 0), (cell_w - 3, cell_h // 2), 1)
    pygame.draw.circle(surf, (0, 0, 0), (cell_w + 1, cell_h // 2), 1)
    frames.append(surf)

    # Frame 2: Walk right
    surf = pygame.Surface((cell_w * 2, cell_h * 2), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 0))
    pygame.draw.circle(surf, (255, 220, 180), (cell_w, cell_h // 2 + 2), cell_w // 2)
    pygame.draw.rect(surf, (0, 150, 255), (cell_w // 2, cell_h, cell_w, cell_h - 2))
    # Eyes looking right
    pygame.draw.circle(surf, (0, 0, 0), (cell_w - 1, cell_h // 2), 1)
    pygame.draw.circle(surf, (0, 0, 0), (cell_w + 3, cell_h // 2), 1)
    frames.append(surf)

    return frames


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

    # Create a pixel sprite from programmatically generated frames
    char_frames = create_character_sprite(cell_w, cell_h)
    pixel_frames = [
        pyunicodegame.PixelFrame(surf, cell_w, cell_h) for surf in char_frames
    ]

    player = pyunicodegame.PixelSprite(pixel_frames)
    player.x = 30
    player.y = 15
    player._teleport_pending = True
    player.lerp_speed = 10
    player.z_index = 10
    root.add_sprite(player)

    # Add animations
    idle_anim = pyunicodegame.create_animation("idle", [0], frame_duration=1.0)
    walk_left = pyunicodegame.create_animation(
        "walk_left",
        [1, 0, 1, 0],
        frame_duration=0.15,
        offsets=[(0, 0), (0, -2), (0, 0), (0, -2)],
    )
    walk_right = pyunicodegame.create_animation(
        "walk_right",
        [2, 0, 2, 0],
        frame_duration=0.15,
        offsets=[(0, 0), (0, -2), (0, 0), (0, -2)],
    )

    player.add_animation(idle_anim)
    player.add_animation(walk_left)
    player.add_animation(walk_right)
    player.play_animation("idle")

    # Create a unicode sprite for comparison (shows grid alignment)
    unicode_sprite = pyunicodegame.create_sprite(
        """
        ##
        ##
        """,
        x=10,
        y=15,
        fg=(255, 100, 100),
    )
    root.add_sprite(unicode_sprite)

    # Create a static pixel sprite
    static_surf = create_test_image(cell_w * 2, cell_h * 2, (100, 255, 100))
    static_frame = pyunicodegame.PixelFrame(static_surf, cell_w, cell_h)
    static_sprite = pyunicodegame.PixelSprite([static_frame])
    static_sprite.x = 50
    static_sprite.y = 15
    static_sprite._teleport_pending = True
    root.add_sprite(static_sprite)

    # Add lighting to see how it affects pixel sprites
    root.set_lighting(ambient=(80, 80, 100))
    light = pyunicodegame.create_light(
        x=30,
        y=15,
        radius=15,
        color=(255, 200, 150),
        intensity=1.0,
        follow_sprite=player,  # Light follows player (via duck typing - uses .x/.y)
    )
    root.add_light(light)

    # Enable bloom
    root.set_bloom(enabled=True, threshold=200, intensity=1.5)

    # Particle frame for effects
    particle_surf = create_particle_sprite(cell_w, cell_h, (255, 200, 50))
    particle_frame = pyunicodegame.PixelFrame(particle_surf, cell_w, cell_h)

    moving_left = False
    moving_right = False

    def update(dt):
        nonlocal moving_left, moving_right

        # Check if movement animation finished and return to idle
        if not player.is_animation_playing():
            if moving_left or moving_right:
                moving_left = False
                moving_right = False
                player.play_animation("idle")

    def on_key(key):
        nonlocal moving_left, moving_right

        if key == pygame.K_LEFT:
            player.move_to(player.x - 1, player.y)
            if not moving_left:
                player.play_animation("walk_left")
                moving_left = True
                moving_right = False
        elif key == pygame.K_RIGHT:
            player.move_to(player.x + 1, player.y)
            if not moving_right:
                player.play_animation("walk_right")
                moving_right = True
                moving_left = False
        elif key == pygame.K_UP:
            player.move_to(player.x, player.y - 1)
        elif key == pygame.K_DOWN:
            player.move_to(player.x, player.y + 1)
        elif key == pygame.K_SPACE:
            # Emit pixel effect particles
            import random

            for _ in range(5):
                effect = pyunicodegame.PixelEffectSprite([particle_frame])
                effect.x = float(player.x) + 1
                effect.y = float(player.y)
                effect.vx = random.uniform(-5, 5)
                effect.vy = random.uniform(-8, -2)
                effect.drag = 0.3
                effect.fade_time = 0.8
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

        # Labels
        root.put_string(9, 14, "Unicode", (150, 150, 150))
        root.put_string(28, 14, "PixelSprite", (150, 150, 150))
        root.put_string(49, 14, "Static", (150, 150, 150))

        # Grid reference
        root.put_string(1, 28, f"Cell size: {cell_w}x{cell_h}px", (80, 80, 80))

    pyunicodegame.run(update=update, render=render, on_key=on_key)


if __name__ == "__main__":
    main()
