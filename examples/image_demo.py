#!/usr/bin/env python3
"""
Demo of image-to-pixel-art conversion using create_sprite_from_image.

Displays an image as a pixel art sprite using half-block characters (▄)
with foreground and background colors for 2 vertical pixels per cell.

Shows both downscaling modes side by side:
- "average" (box filter) - smooth color blending
- "mode" (most frequent color) - preserves hard edges
"""

import argparse
import pygame
import pyunicodegame

# Default test image
DEFAULT_IMAGE = "examples/The_Persistence_of_Memory.jpg"


def main():
    parser = argparse.ArgumentParser(description="Image to pixel art demo")
    parser.add_argument("image", nargs="?", default=DEFAULT_IMAGE, help="Path to image file")
    parser.add_argument("--width", type=int, default=60, help="Output width in pixels per image")
    parser.add_argument("--height", type=int, default=40, help="Output height in pixels per image")
    args = parser.parse_args()

    # Calculate window size for two images side by side
    # Width: image + gap + image + margins
    win_width = args.width * 2 + 5
    win_height = (args.height + 1) // 2 + 5

    root = pyunicodegame.init(
        "Image Demo - Downscaling Modes",
        width=win_width,
        height=win_height,
        bg=(10, 10, 20, 255)
    )

    # Create sprite with "average" mode (box filter)
    sprite_avg = pyunicodegame.create_sprite_from_image(
        args.image,
        width=args.width,
        height=args.height,
        x=1,
        y=2,
        mode="average",
    )
    root.add_sprite(sprite_avg)

    # Create sprite with "mode" mode (most frequent color)
    sprite_mode = pyunicodegame.create_sprite_from_image(
        args.image,
        width=args.width,
        height=args.height,
        x=args.width + 4,
        y=2,
        mode="mode",
    )
    root.add_sprite(sprite_mode)

    def render():
        # Labels
        root.put_string(1, 1, "average (box filter)", (150, 150, 150))
        root.put_string(args.width + 4, 1, "mode (most frequent)", (150, 150, 150))
        # Info at bottom
        info = f"{args.width}x{args.height}px | Q to quit"
        root.put_string(1, win_height - 2, info, (80, 80, 80))

    def on_key(key):
        if key == pygame.K_q:
            pyunicodegame.quit()

    pyunicodegame.run(render=render, on_key=on_key)


if __name__ == "__main__":
    main()
