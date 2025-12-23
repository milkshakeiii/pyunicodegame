#!/usr/bin/env python3
"""
Demo of the lighting system with shadow casting.

WASD to move player, arrow keys to move light.
Press L to toggle lighting, B to toggle bloom.
"""

import pygame
import pyunicodegame


def main():
    root = pyunicodegame.init("Lighting Demo", width=60, height=30, bg=(10, 10, 15, 255))

    # Create player
    player = pyunicodegame.create_sprite("@", fg=(255, 255, 255))
    player.move_to(30, 15)
    root.add_sprite(player)

    # Player's torch - warm light that follows player
    torch = pyunicodegame.create_light(
        x=30, y=15,
        radius=12,
        color=(255, 180, 100),  # Warm orange
        intensity=1.0,
        falloff=1.5,
        follow_sprite=player,
    )
    root.add_light(torch)

    # Static blue light (magic crystal)
    crystal_light = pyunicodegame.create_light(
        x=45, y=8,
        radius=8,
        color=(100, 150, 255),  # Blue
        intensity=0.8,
        falloff=1.0,
    )
    root.add_light(crystal_light)

    # Crystal sprite
    crystal = pyunicodegame.create_sprite("*", fg=(150, 200, 255))
    crystal.move_to(45, 8)
    root.add_sprite(crystal)

    # Create some walls that block light
    walls = []
    wall_positions = [
        # Vertical wall
        (25, 10), (25, 11), (25, 12), (25, 13), (25, 14),
        # Horizontal wall
        (35, 18), (36, 18), (37, 18), (38, 18), (39, 18), (40, 18),
        # Corner
        (15, 20), (16, 20), (17, 20),
        (15, 21), (15, 22),
        # Box
        (50, 12), (51, 12), (52, 12),
        (50, 13), (52, 13),
        (50, 14), (51, 14), (52, 14),
    ]

    for wx, wy in wall_positions:
        wall = pyunicodegame.create_sprite("#", fg=(100, 100, 100), blocks_light=True)
        wall.move_to(wx, wy)
        root.add_sprite(wall)
        walls.append(wall)

    # Optional: customize ambient
    root.set_lighting(ambient=(15, 15, 25))

    def on_key(key):
        # Player movement
        if key == pygame.K_w:
            player.move_to(player.x, player.y - 1)
        elif key == pygame.K_s:
            player.move_to(player.x, player.y + 1)
        elif key == pygame.K_a:
            player.move_to(player.x - 1, player.y)
        elif key == pygame.K_d:
            player.move_to(player.x + 1, player.y)
        # Toggle lighting
        elif key == pygame.K_l:
            root._lighting_enabled = not root._lighting_enabled
        # Toggle bloom
        elif key == pygame.K_b:
            if root._bloom_enabled:
                root.set_bloom(enabled=False)
            else:
                root.set_bloom(enabled=True, threshold=150, intensity=1.5)
        elif key == pygame.K_q:
            pyunicodegame.quit()

    def render():
        # Draw floor tiles
        for y in range(2, 28):
            for x in range(2, 58):
                root.put(x, y, '.', (40, 40, 50))

        # Instructions
        root.put_string(2, 0, "WASD: move   L: toggle light   B: toggle bloom   Q: quit", (100, 100, 100))

        # Status
        light_status = "ON" if root._lighting_enabled else "OFF"
        bloom_status = "ON" if root._bloom_enabled else "OFF"
        root.put_string(2, 29, f"Lighting: {light_status}  Bloom: {bloom_status}", (80, 80, 80))

    pyunicodegame.run(render=render, on_key=on_key)


if __name__ == "__main__":
    main()
