#!/usr/bin/env python3
"""
Demo of the Animation system.

Use arrow keys to move (triggers walk animation with bobbing).
Press SPACE to jump (one-shot animation).
Press S to stop animations.
"""

import pygame
import pyunicodegame


def main():
    root = pyunicodegame.init("Animation Demo", width=50, height=20, bg=(10, 10, 30, 255))

    # Create a player sprite with multiple frames
    # Frame 0: Standing
    player = pyunicodegame.create_sprite('''
        O
       /|\\
       / \\
    ''', fg=(0, 255, 100), char_colors={'O': (255, 220, 180)})

    # Frame 1: Walk left foot forward
    player.add_frame('''
        O
       /|\\
       /
    ''')

    # Frame 2: Walk right foot forward
    player.add_frame('''
        O
       /|\\
         \\
    ''')

    # Frame 3: Jump pose
    player.add_frame('''
       \\O/
        |
       / \\
    ''')

    player.move_to(25, 12)
    player.lerp_speed = 8  # cells per second

    # Create walk animation with bobbing offset
    walk = pyunicodegame.create_animation(
        "walk",
        frame_indices=[0, 1, 0, 2],  # Stand, left, stand, right
        frame_duration=0.15,
        offsets=[(0, 0), (0, -2), (0, 0), (0, -2)],  # Bob up on step frames
        loop=True,
        offset_speed=80.0  # pixels/sec for smooth offset transition
    )
    player.add_animation(walk)

    # Create idle animation (subtle breathing)
    idle = pyunicodegame.create_animation(
        "idle",
        frame_indices=[0, 0],
        frame_duration=0.8,
        offsets=[(0, 0), (0, -1)],  # Subtle rise
        loop=True,
        offset_speed=20.0
    )
    player.add_animation(idle)

    # Create jump animation (one-shot)
    jump = pyunicodegame.create_animation(
        "jump",
        frame_indices=[0, 3, 3, 3, 0],
        frame_duration=0.1,
        offsets=[(0, 0), (0, -8), (0, -12), (0, -8), (0, 0)],  # Arc upward
        loop=False,
        offset_speed=150.0
    )
    player.add_animation(jump)

    # Start with idle animation
    player.play_animation("idle")

    root.add_sprite(player)

    def on_key(key):
        if key == pygame.K_LEFT:
            player.move_to(player.x - 1, player.y)
            if not player.is_animation_playing("jump"):
                player.play_animation("walk", reset=False)
        elif key == pygame.K_RIGHT:
            player.move_to(player.x + 1, player.y)
            if not player.is_animation_playing("jump"):
                player.play_animation("walk", reset=False)
        elif key == pygame.K_UP:
            player.move_to(player.x, player.y - 1)
            if not player.is_animation_playing("jump"):
                player.play_animation("walk", reset=False)
        elif key == pygame.K_DOWN:
            player.move_to(player.x, player.y + 1)
            if not player.is_animation_playing("jump"):
                player.play_animation("walk", reset=False)
        elif key == pygame.K_SPACE:
            player.play_animation("jump")
        elif key == pygame.K_s:
            player.stop_animation()
        elif key == pygame.K_q:
            pyunicodegame.quit()

    def update(dt):
        # Return to idle when jump finishes
        if player.is_animation_finished():
            player.play_animation("idle")

    def render():
        # Draw ground
        for x in range(root.width):
            root.put(x, 15, "━", (80, 60, 40))

        # Instructions
        root.put_string(1, 1, "Arrow keys: move (walk animation)", (100, 100, 100))
        root.put_string(1, 2, "SPACE: jump, S: stop, Q: quit", (100, 100, 100))

        # Show current animation state
        if player._current_animation:
            state = f"Animation: {player._current_animation}"
            if player.is_animation_finished():
                state += " (finished)"
            root.put_string(1, 18, state, (150, 150, 100))

    pyunicodegame.run(update=update, render=render, on_key=on_key)


if __name__ == "__main__":
    main()
