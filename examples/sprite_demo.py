#!/usr/bin/env python3
"""
Demo of the unicode sprite system.

Use arrow keys to move the player. The sprite smoothly interpolates between cells.
"""

import pygame
import pyunicodegame


def main():
    root = pyunicodegame.init("Sprite Demo", width=40, height=20, bg=(10, 10, 30, 255))

    # Create a player sprite
    player = pyunicodegame.create_sprite('''
        O
       /|\\
       / \\
    ''', x=20, y=10, fg=(0, 255, 100), char_colors={'O': (255, 220, 180)}, lerp_speed=10)

    root.add_sprite(player)

    # Create some scenery sprites
    tree = pyunicodegame.create_sprite('''
        *
       /|\\
        |
    ''', x=5, y=10, fg=(0, 180, 60), char_colors={'*': (100, 255, 100)})
    root.add_sprite(tree)

    tree2 = pyunicodegame.create_sprite('''
        *
       /|\\
        |
    ''', x=35, y=8, fg=(0, 150, 50), char_colors={'*': (80, 220, 80)})
    root.add_sprite(tree2)

    def on_key(key):
        if key == pygame.K_LEFT:
            player.move_to(player.x - 1, player.y)
        elif key == pygame.K_RIGHT:
            player.move_to(player.x + 1, player.y)
        elif key == pygame.K_UP:
            player.move_to(player.x, player.y - 1)
        elif key == pygame.K_DOWN:
            player.move_to(player.x, player.y + 1)
        elif key == pygame.K_q:
            pyunicodegame.quit()

    def render():
        # Draw ground
        for x in range(root.width):
            root.put(x, 13, "─", (60, 40, 20))

        # Instructions
        root.put_string(1, 1, "Arrow keys to move, Q to quit", (100, 100, 100))

    pyunicodegame.run(render=render, on_key=on_key)


if __name__ == "__main__":
    main()
