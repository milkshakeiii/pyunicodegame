#!/usr/bin/env python3
"""
Demo of Legacy Computing wedge characters (U+1FB3C-U+1FB67).

Shows the 44 wedge characters and demonstrates using them to draw smooth shapes.
"""

import argparse
import pygame
import pyunicodegame

FONTS = ["5x8", "6x13", "9x18", "10x20"]


def main():
    parser = argparse.ArgumentParser(description="Wedge characters demo")
    parser.add_argument("--font", choices=FONTS, default="10x20", help="Font size to use")
    args = parser.parse_args()

    root = pyunicodegame.init("Wedge Characters Demo", width=80, height=30, bg=(10, 10, 30, 255), font_name=args.font)

    def render():
        # Title
        root.put_string(2, 1, "Legacy Computing Wedge Characters (U+1FB3C-U+1FB67)", (200, 200, 255))

        # Show all 44 wedge characters in a grid
        root.put_string(2, 3, "Base wedges (22):", (150, 150, 150))
        for i in range(22):
            char = chr(0x1FB3C + i)
            x = 2 + (i % 11) * 3
            y = 4 + (i // 11) * 2
            root.put(x, y, char, (255, 255, 255))
            # Show codepoint below
            root.put_string(x, y + 1, f"{i:02d}", (80, 80, 80))

        root.put_string(2, 8, "Inverted wedges (22):", (150, 150, 150))
        for i in range(22):
            char = chr(0x1FB3C + 22 + i)
            x = 2 + (i % 11) * 3
            y = 9 + (i // 11) * 2
            root.put(x, y, char, (255, 255, 255))

        # Demo: Rounded rectangle using wedges
        root.put_string(2, 14, "Rounded rectangle example:", (150, 150, 150))

        # Small rounded rect
        rx, ry = 4, 16
        color = (100, 200, 100)
        # Corners: use large fills WITH cutouts (not small triangles)
        # TL corner: large fill with TL cutout = index 5 (left_2_3->top_mid, fills below)
        root.put(rx, ry, chr(0x1FB3C + 5), color)  # TL corner
        # TR corner: large fill with TR cutout = index 16 (top_mid->right_2_3, fills below)
        root.put(rx + 8, ry, chr(0x1FB3C + 16), color)  # TR corner
        # BL corner: large fill with BL cutout = inverted of small BL = index 22
        root.put(rx, ry + 3, chr(0x1FB3C + 22), color)  # BL corner
        # BR corner: large fill with BR cutout = inverted of small BR = index 33
        root.put(rx + 8, ry + 3, chr(0x1FB3C + 33), color)  # BR corner
        # Edges
        for x in range(rx + 1, rx + 8):
            root.put(x, ry, chr(0x2588), color)  # Top edge (full block)
            root.put(x, ry + 3, chr(0x2588), color)  # Bottom edge
        for y in range(ry + 1, ry + 3):
            root.put(rx, y, chr(0x2588), color)  # Left edge
            root.put(rx + 8, y, chr(0x2588), color)  # Right edge
        # Fill
        for y in range(ry + 1, ry + 3):
            for x in range(rx + 1, rx + 8):
                root.put(x, y, chr(0x2588), color)

        # Demo: Diagonal line (going down-right)
        root.put_string(30, 14, "Diagonal line:", (150, 150, 150))

        # Alternating wedge pairs for smooth diagonal:
        # Even rows: 🭦🭐 (indices 42, 20)
        # Odd rows: 🭖🭀 (indices 26, 4), indented by 1
        dx, dy = 32, 16
        color2 = (200, 150, 100)
        for i in range(6):
            x_off = i // 2 + (i % 2)
            if i % 2 == 0:
                root.put(dx + x_off, dy + i, chr(0x1FB3C + 42), color2)  # 🭦
                root.put(dx + x_off + 1, dy + i, chr(0x1FB3C + 20), color2)  # 🭐
            else:
                root.put(dx + x_off, dy + i, chr(0x1FB3C + 26), color2)  # 🭖
                root.put(dx + x_off + 1, dy + i, chr(0x1FB3C + 4), color2)  # 🭀

        # Demo: Show some paired wedges that combine to full block
        root.put_string(2, 22, "Wedge pairs (base + inverted = full block):", (150, 150, 150))
        # Each base wedge + its inverted counterpart = full block
        pairs = [(0, 22), (1, 23), (5, 27), (11, 33), (16, 38)]
        for idx, (a, b) in enumerate(pairs):
            x = 4 + idx * 8
            root.put(x, 24, chr(0x1FB3C + a), (255, 200, 100))
            root.put(x + 1, 24, "+", (100, 100, 100))
            root.put(x + 2, 24, chr(0x1FB3C + b), (255, 200, 100))
            root.put(x + 3, 24, "=", (100, 100, 100))
            root.put(x + 4, 24, chr(0x2588), (255, 200, 100))

        root.put_string(2, 28, "Press Q to quit", (80, 80, 80))

    def on_key(key):
        if key == pygame.K_q:
            pyunicodegame.quit()

    pyunicodegame.run(render=render, on_key=on_key)


if __name__ == "__main__":
    main()
