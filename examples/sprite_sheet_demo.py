#!/usr/bin/env python3
"""
Demo of the SpriteSheet system.

Demonstrates:
- Loading a sprite sheet from an image file
- Extracting frames for different animations
- Animation state machine (idle, walk, run, bark)
- Sprite flipping for left/right facing
- Simple side-scrolling platformer scene
- Floating-point positions for smooth sub-cell movement

Note: This demo uses floating-point positions with move_to(teleport=True)
for smooth continuous movement. For cell-based movement with lerp smoothing,
see animation_demo.py which uses integer positions with lerp_speed.

Controls:
- Left/Right arrows: Walk
- Shift + Left/Right: Run
- Space: Bark
- Q: Quit
"""

import pygame
import pyunicodegame


def main():
    # Initialize with 10x20 font (matches 30x20 sprite frames = 3 cells wide)
    root = pyunicodegame.init(
        "Sprite Sheet Demo",
        width=50,
        height=18,
        bg=(135, 206, 235, 255),  # Sky blue
        font_name="10x20",
    )

    cell_w, cell_h = root.cell_size

    # Load sprite sheet: 3 rows x 4 cols, 30x20 per frame
    sheet = pyunicodegame.create_sprite_sheet(
        "examples/30x20_german_shepherd.png",
        frame_width=30,
        frame_height=20,
        rows=3,
        cols=4,
    )

    # Get all frames - original sprite faces left
    left_frames = [sheet.get_frame(i) for i in range(12)]

    # Create flipped frames (right-facing)
    right_frames = []
    for frame in left_frames:
        flipped_surf = pygame.transform.flip(frame.surface, True, False)
        right_frames.append(pyunicodegame.PixelFrame(flipped_surf, cell_w, cell_h))

    # Create dog sprite with right-facing frames initially
    dog = pyunicodegame.PixelSprite(right_frames)

    # Ground position
    ground_y = 14

    # Position dog on ground (sprite is 1 cell tall)
    dog.move_to(10, ground_y - 1, teleport=True)
    root.add_sprite(dog)

    # Create animations
    # Row 0 (frames 0-3): Bark
    # Row 1 (frames 4-7): Walk
    # Row 2 (frames 8-11): Run
    idle = pyunicodegame.create_animation("idle", [0], frame_duration=1.0, loop=True)
    bark = pyunicodegame.create_animation("bark", [0, 1, 2, 3, 2, 1], frame_duration=0.1, loop=False)
    walk = pyunicodegame.create_animation("walk", [4, 5, 6, 7], frame_duration=0.12, loop=True)
    run = pyunicodegame.create_animation("run", [8, 9, 10, 11], frame_duration=0.08, loop=True)

    dog.add_animation(idle)
    dog.add_animation(bark)
    dog.add_animation(walk)
    dog.add_animation(run)
    dog.play_animation("idle")

    # State
    facing_right = True
    barking = False

    # Movement speeds (cells per second)
    walk_speed = 8
    run_speed = 16

    def set_facing(right: bool):
        nonlocal facing_right
        if right != facing_right:
            facing_right = right
            dog.frames = right_frames if right else left_frames

    def update(dt):
        nonlocal barking

        # Check if bark animation finished
        if barking and dog.is_animation_finished():
            barking = False

        # Handle continuous movement based on held keys
        if not barking:
            keys = pygame.key.get_pressed()
            shift_held = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
            moving_left = keys[pygame.K_LEFT]
            moving_right = keys[pygame.K_RIGHT]

            if moving_left and not moving_right:
                set_facing(False)
                speed = run_speed if shift_held else walk_speed
                new_x = dog.x - speed * dt
                dog.move_to(new_x, dog.y, teleport=True)
                anim = "run" if shift_held else "walk"
                if not dog.is_animation_playing(anim):
                    dog.play_animation(anim)

            elif moving_right and not moving_left:
                set_facing(True)
                speed = run_speed if shift_held else walk_speed
                new_x = dog.x + speed * dt
                dog.move_to(new_x, dog.y, teleport=True)
                anim = "run" if shift_held else "walk"
                if not dog.is_animation_playing(anim):
                    dog.play_animation(anim)

            else:
                # Not moving
                if not dog.is_animation_playing("idle"):
                    dog.play_animation("idle")

    def on_key(key):
        nonlocal barking

        if key == pygame.K_SPACE:
            if not barking:
                barking = True
                dog.play_animation("bark")

        elif key == pygame.K_q:
            pyunicodegame.quit()

    def render():
        # Draw ground
        for x in range(root.width):
            root.put(x, ground_y, "█", (34, 139, 34))  # Forest green grass top
            for y in range(ground_y + 1, root.height):
                root.put(x, y, "█", (139, 90, 43))  # Brown dirt

        # Draw some simple clouds
        root.put_string(3, 3, "_.--._", (255, 255, 255))
        root.put_string(2, 4, "(      )", (255, 255, 255))
        root.put_string(3, 5, "`----'", (255, 255, 255))

        root.put_string(38, 2, "_.--._", (255, 255, 255))
        root.put_string(37, 3, "(      )", (255, 255, 255))
        root.put_string(38, 4, "`----'", (255, 255, 255))

        root.put_string(22, 4, "_.-._", (255, 255, 255))
        root.put_string(21, 5, "(     )", (255, 255, 255))
        root.put_string(22, 6, "`---'", (255, 255, 255))

        # Instructions
        root.put_string(1, 1, "Arrows: walk, Shift+Arrows: run, Space: bark", (50, 50, 50))
        root.put_string(1, 2, "Q: quit", (50, 50, 50))

    pyunicodegame.run(update=update, render=render, on_key=on_key)


if __name__ == "__main__":
    main()
