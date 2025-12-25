#!/usr/bin/env python3
"""
Demo of Legacy Computing wedge characters (U+1FB3C-U+1FB67).

Shows the 44 wedge characters and demonstrates using them to draw smooth shapes.

================================================================================
WEDGE CHARACTER REFERENCE FOR LLMs
================================================================================

These 44 characters (22 base + 22 inverted) allow drawing smooth diagonal lines
and rounded shapes in terminal/text UIs. Each is defined by a diagonal line
that divides the cell, with one side filled.

STRUCTURE:
- Base wedges (indices 0-21, U+1FB3C-U+1FB51): Fill BELOW the diagonal line
- Inverted wedges (indices 22-43, U+1FB52-U+1FB67): Fill ABOVE the same line
  Index N+22 is the inverse of index N (together they make a full block).

HOW WEDGES ARE DEFINED:
Each wedge has a diagonal line from point_a to point_b. The difference between
base and inverted is simply which side of that line is filled.

Edge points used in definitions:
  - Corners: TL, TR, BL, BR
  - Edge midpoints: top_mid, bot_mid
  - Vertical 1/3 points: left_1_3, left_2_3, right_1_3, right_2_3
    (1_3 = 1/3 up from bottom, 2_3 = 2/3 up from bottom)

CONNECTION RULES:
Two wedges connect smoothly when their shared edge matches. There are two ways:

1. FULL EDGE CONNECTION: A wedge with a fully-filled edge connects to any
   wedge with a fully-filled opposite edge (including full block).

2. POINT MATCHING: Wedges connect when their diagonals meet at corresponding
   points AND the fill is on the same side of that point. Specifically:
   - pa<->pa: Both diagonals START at corresponding points
   - pb<->pb: Both diagonals END at corresponding points
   - pa<->pb: One starts where the other ends at corresponding points
   The fill must be on the same side (e.g., both LEFT of the mid-point).

CONNECTIVITY MAP:
Format: [index] char  L:left R:right T:top B:bottom connections
        █ = has full edge (connects to full block and all full opposite edges)

[ 0] 🬼  L:🭇🭈🭎🭏🭑  B:🭌🭎🭐🭗🭙🭛
[ 1] 🬽  L:🭇🭈🭎🭏🭑  B:█🭒🭓🭔🭕🭖🭘🭚🭜🭝🭞🭟🭠🭡🭣🭥🭧
[ 2] 🬾  L:🭆🭉🭊🭌🭍  B:🭌🭎🭐🭗🭙🭛
[ 3] 🬿  L:🭆🭉🭊🭌🭍  B:█🭒🭓🭔🭕🭖🭘🭚🭜🭝🭞🭟🭠🭡🭣🭥🭧
[ 4] 🭀  L:█🭁🭂🭃🭄🭅🭋🭒🭓🭔🭕🭖🭦  B:🭌🭎🭐🭗🭙🭛
[ 5] 🭁  L:🭆🭉🭊🭌🭍  R:█🭀🭌🭍🭎🭏🭐🭛🭝🭞🭟🭠🭡  T:🭇🭉🭋🭒🭔🭖  B:█🭒🭓🭔🭕🭖🭘🭚🭜🭝🭞🭟🭠🭡🭣🭥🭧
[ 6] 🭂  L:🭆🭉🭊🭌🭍  R:█🭀🭌🭍🭎🭏🭐🭛🭝🭞🭟🭠🭡  B:█🭒🭓🭔🭕🭖🭘🭚🭜🭝🭞🭟🭠🭡🭣🭥🭧
[ 7] 🭃  L:🭇🭈🭎🭏🭑  R:█🭀🭌🭍🭎🭏🭐🭛🭝🭞🭟🭠🭡  T:🭇🭉🭋🭒🭔🭖  B:█🭒🭓🭔🭕🭖🭘🭚🭜🭝🭞🭟🭠🭡🭣🭥🭧
[ 8] 🭄  L:🭇🭈🭎🭏🭑  R:█🭀🭌🭍🭎🭏🭐🭛🭝🭞🭟🭠🭡  B:█🭒🭓🭔🭕🭖🭘🭚🭜🭝🭞🭟🭠🭡🭣🭥🭧
[ 9] 🭅  R:█🭀🭌🭍🭎🭏🭐🭛🭝🭞🭟🭠🭡  T:🭇🭉🭋🭒🭔🭖  B:█🭒🭓🭔🭕🭖🭘🭚🭜🭝🭞🭟🭠🭡🭣🭥🭧
[10] 🭆  L:🭇🭈🭎🭏🭑  R:🬾🬿🭁🭂🭑  B:█🭒🭓🭔🭕🭖🭘🭚🭜🭝🭞🭟🭠🭡🭣🭥🭧
[11] 🭇  R:🬼🬽🭃🭄🭆  B:🭁🭃🭅🭢🭤🭦
[12] 🭈  R:🬼🬽🭃🭄🭆  B:█🭒🭓🭔🭕🭖🭘🭚🭜🭝🭞🭟🭠🭡🭣🭥🭧
[13] 🭉  R:🬾🬿🭁🭂🭑  B:🭁🭃🭅🭢🭤🭦
[14] 🭊  R:🬾🬿🭁🭂🭑  B:█🭒🭓🭔🭕🭖🭘🭚🭜🭝🭞🭟🭠🭡🭣🭥🭧
[15] 🭋  R:█🭀🭌🭍🭎🭏🭐🭛🭝🭞🭟🭠🭡  B:🭁🭃🭅🭢🭤🭦
[16] 🭌  L:█🭁🭂🭃🭄🭅🭋🭒🭓🭔🭕🭖🭦  R:🬾🬿🭁🭂🭑  T:🬼🬾🭀🭝🭟🭡  B:█🭒🭓🭔🭕🭖🭘🭚🭜🭝🭞🭟🭠🭡🭣🭥🭧
[17] 🭍  L:█🭁🭂🭃🭄🭅🭋🭒🭓🭔🭕🭖🭦  R:🬾🬿🭁🭂🭑  B:█🭒🭓🭔🭕🭖🭘🭚🭜🭝🭞🭟🭠🭡🭣🭥🭧
[18] 🭎  L:█🭁🭂🭃🭄🭅🭋🭒🭓🭔🭕🭖🭦  R:🬼🬽🭃🭄🭆  T:🬼🬾🭀🭝🭟🭡  B:█🭒🭓🭔🭕🭖🭘🭚🭜🭝🭞🭟🭠🭡🭣🭥🭧
[19] 🭏  L:█🭁🭂🭃🭄🭅🭋🭒🭓🭔🭕🭖🭦  R:🬼🬽🭃🭄🭆  B:█🭒🭓🭔🭕🭖🭘🭚🭜🭝🭞🭟🭠🭡🭣🭥🭧
[20] 🭐  L:█🭁🭂🭃🭄🭅🭋🭒🭓🭔🭕🭖🭦  T:🬼🬾🭀🭝🭟🭡  B:█🭒🭓🭔🭕🭖🭘🭚🭜🭝🭞🭟🭠🭡🭣🭥🭧
[21] 🭑  L:🭆🭉🭊🭌🭍  R:🬼🬽🭃🭄🭆  B:█🭒🭓🭔🭕🭖🭘🭚🭜🭝🭞🭟🭠🭡🭣🭥🭧
[22] 🭒  L:🭝🭞🭤🭥🭧  R:█🭀🭌🭍🭎🭏🭐🭛🭝🭞🭟🭠🭡  T:█🬽🬿🭁🭂🭃🭄🭅🭆🭈🭊🭌🭍🭎🭏🭐🭑  B:🭁🭃🭅🭢🭤🭦
[23] 🭓  L:🭝🭞🭤🭥🭧  R:█🭀🭌🭍🭎🭏🭐🭛🭝🭞🭟🭠🭡  T:█🬽🬿🭁🭂🭃🭄🭅🭆🭈🭊🭌🭍🭎🭏🭐🭑
[24] 🭔  L:🭜🭟🭠🭢🭣  R:█🭀🭌🭍🭎🭏🭐🭛🭝🭞🭟🭠🭡  T:█🬽🬿🭁🭂🭃🭄🭅🭆🭈🭊🭌🭍🭎🭏🭐🭑  B:🭁🭃🭅🭢🭤🭦
[25] 🭕  L:🭜🭟🭠🭢🭣  R:█🭀🭌🭍🭎🭏🭐🭛🭝🭞🭟🭠🭡  T:█🬽🬿🭁🭂🭃🭄🭅🭆🭈🭊🭌🭍🭎🭏🭐🭑
[26] 🭖  R:█🭀🭌🭍🭎🭏🭐🭛🭝🭞🭟🭠🭡  T:█🬽🬿🭁🭂🭃🭄🭅🭆🭈🭊🭌🭍🭎🭏🭐🭑  B:🭁🭃🭅🭢🭤🭦
[27] 🭗  L:🭜🭟🭠🭢🭣  T:🬼🬾🭀🭝🭟🭡
[28] 🭘  L:🭜🭟🭠🭢🭣  T:█🬽🬿🭁🭂🭃🭄🭅🭆🭈🭊🭌🭍🭎🭏🭐🭑
[29] 🭙  L:🭝🭞🭤🭥🭧  T:🬼🬾🭀🭝🭟🭡
[30] 🭚  L:🭝🭞🭤🭥🭧  T:█🬽🬿🭁🭂🭃🭄🭅🭆🭈🭊🭌🭍🭎🭏🭐🭑
[31] 🭛  L:█🭁🭂🭃🭄🭅🭋🭒🭓🭔🭕🭖🭦  T:🬼🬾🭀🭝🭟🭡
[32] 🭜  L:🭝🭞🭤🭥🭧  R:🭔🭕🭗🭘🭧  T:█🬽🬿🭁🭂🭃🭄🭅🭆🭈🭊🭌🭍🭎🭏🭐🭑
[33] 🭝  L:█🭁🭂🭃🭄🭅🭋🭒🭓🭔🭕🭖🭦  R:🭒🭓🭙🭚🭜  T:█🬽🬿🭁🭂🭃🭄🭅🭆🭈🭊🭌🭍🭎🭏🭐🭑  B:🭌🭎🭐🭗🭙🭛
[34] 🭞  L:█🭁🭂🭃🭄🭅🭋🭒🭓🭔🭕🭖🭦  R:🭒🭓🭙🭚🭜  T:█🬽🬿🭁🭂🭃🭄🭅🭆🭈🭊🭌🭍🭎🭏🭐🭑
[35] 🭟  L:█🭁🭂🭃🭄🭅🭋🭒🭓🭔🭕🭖🭦  R:🭔🭕🭗🭘🭧  T:█🬽🬿🭁🭂🭃🭄🭅🭆🭈🭊🭌🭍🭎🭏🭐🭑  B:🭌🭎🭐🭗🭙🭛
[36] 🭠  L:█🭁🭂🭃🭄🭅🭋🭒🭓🭔🭕🭖🭦  R:🭔🭕🭗🭘🭧  T:█🬽🬿🭁🭂🭃🭄🭅🭆🭈🭊🭌🭍🭎🭏🭐🭑
[37] 🭡  L:█🭁🭂🭃🭄🭅🭋🭒🭓🭔🭕🭖🭦  T:█🬽🬿🭁🭂🭃🭄🭅🭆🭈🭊🭌🭍🭎🭏🭐🭑  B:🭌🭎🭐🭗🭙🭛
[38] 🭢  R:🭔🭕🭗🭘🭧  T:🭇🭉🭋🭒🭔🭖
[39] 🭣  R:🭔🭕🭗🭘🭧  T:█🬽🬿🭁🭂🭃🭄🭅🭆🭈🭊🭌🭍🭎🭏🭐🭑
[40] 🭤  R:🭒🭓🭙🭚🭜  T:🭇🭉🭋🭒🭔🭖
[41] 🭥  R:🭒🭓🭙🭚🭜  T:█🬽🬿🭁🭂🭃🭄🭅🭆🭈🭊🭌🭍🭎🭏🭐🭑
[42] 🭦  R:█🭀🭌🭍🭎🭏🭐🭛🭝🭞🭟🭠🭡  T:🭇🭉🭋🭒🭔🭖
[43] 🭧  L:🭜🭟🭠🭢🭣  R:🭒🭓🭙🭚🭜  T:█🬽🬿🭁🭂🭃🭄🭅🭆🭈🭊🭌🭍🭎🭏🭐🭑

COMMON PATTERNS:

Rounded rectangle corners (these have full right+bottom or left+top edges):
  TL: 🭁 (5)   TR: 🭌 (16)   BL: 🭒 (22)   BR: 🭝 (33)

Diagonal line going DOWN-RIGHT (alternating 2-cell pattern):
  Even rows: 🭦🭐 (42, 20)
  Odd rows:  🭖🭀 (26, 4) - shifted right by 1

Full block: █ (U+2588) - connects to any wedge with a full edge on that side

================================================================================
"""

import argparse
import pygame
import pyunicodegame

FONTS = ["5x8", "6x13", "9x18", "10x20"]


def main():
    parser = argparse.ArgumentParser(description="Wedge characters demo")
    parser.add_argument("--font", choices=FONTS, default="10x20", help="Font size to use")
    args = parser.parse_args()

    root = pyunicodegame.init("Wedge Characters Demo", width=80, height=40, bg=(10, 10, 30, 255), font_name=args.font)

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

        # Demo: Diagonal line going down-left
        root.put_string(50, 14, "Diagonal (down-left):", (150, 150, 150))
        dx2, dy2 = 62, 16
        color3 = (150, 200, 100)
        for i in range(6):
            x_off = i // 2 + (i % 2)
            if i % 2 == 0:
                root.put(dx2 - x_off - 1, dy2 + i, chr(0x1FB3C + 41), color3)  # 🭥
                root.put(dx2 - x_off, dy2 + i, chr(0x1FB3C + 15), color3)      # 🭏
            else:
                root.put(dx2 - x_off - 1, dy2 + i, chr(0x1FB3C + 31), color3)  # 🭛
                root.put(dx2 - x_off, dy2 + i, chr(0x1FB3C + 9), color3)       # 🭉

        # Demo: Small circle (3 cells wide)
        root.put_string(2, 26, "Circle:", (150, 150, 150))
        cx, cy = 4, 28
        color4 = (200, 100, 200)
        # Top row: TL corner, full, TR corner
        root.put(cx, cy, chr(0x1FB3C + 5), color4)      # TL
        root.put(cx + 1, cy, chr(0x2588), color4)       # full
        root.put(cx + 2, cy, chr(0x1FB3C + 16), color4) # TR
        # Middle row: full blocks
        root.put(cx, cy + 1, chr(0x2588), color4)
        root.put(cx + 1, cy + 1, chr(0x2588), color4)
        root.put(cx + 2, cy + 1, chr(0x2588), color4)
        # Bottom row: BL corner, full, BR corner
        root.put(cx, cy + 2, chr(0x1FB3C + 22), color4)  # BL (inverted)
        root.put(cx + 1, cy + 2, chr(0x2588), color4)    # full
        root.put(cx + 2, cy + 2, chr(0x1FB3C + 33), color4)  # BR (inverted)

        # Demo: Triangle pointing right
        root.put_string(12, 26, "Triangle:", (150, 150, 150))
        tx, ty = 14, 28
        color5 = (100, 200, 200)
        root.put(tx, ty, chr(0x1FB3C + 15), color5)      # 🭏 top
        root.put(tx, ty + 1, chr(0x2588), color5)        # full middle
        root.put(tx + 1, ty + 1, chr(0x1FB3C + 20), color5)  # 🭐 point
        root.put(tx, ty + 2, chr(0x1FB3C + 9), color5)   # 🭉 bottom

        # Demo: Arrow pointing right
        root.put_string(24, 26, "Arrow:", (150, 150, 150))
        ax, ay = 26, 28
        color6 = (255, 200, 100)
        # Shaft
        root.put(ax, ay + 1, chr(0x2588), color6)
        root.put(ax + 1, ay + 1, chr(0x2588), color6)
        # Arrowhead
        root.put(ax + 2, ay, chr(0x1FB3C + 15), color6)      # top of head
        root.put(ax + 2, ay + 1, chr(0x2588), color6)
        root.put(ax + 3, ay + 1, chr(0x1FB3C + 20), color6)  # point
        root.put(ax + 2, ay + 2, chr(0x1FB3C + 9), color6)   # bottom of head

        # Demo: Speech bubble tail
        root.put_string(36, 26, "Speech tail:", (150, 150, 150))
        sx, sy = 38, 28
        color7 = (200, 200, 200)
        root.put(sx, sy, chr(0x2588), color7)
        root.put(sx + 1, sy, chr(0x2588), color7)
        root.put(sx + 2, sy, chr(0x2588), color7)
        root.put(sx, sy + 1, chr(0x2588), color7)
        root.put(sx + 1, sy + 1, chr(0x1FB3C + 22), color7)  # BL corner starts tail
        root.put(sx + 1, sy + 2, chr(0x1FB3C + 4), color7)   # tail point

        root.put_string(2, 38, "Press Q to quit", (80, 80, 80))

    def on_key(key):
        if key == pygame.K_q:
            pyunicodegame.quit()

    pyunicodegame.run(render=render, on_key=on_key)


if __name__ == "__main__":
    main()
