#!/usr/bin/env python3
"""
Unifont Demo - Showcasing Unicode Coverage

Demonstrates the wide range of characters available in GNU Unifont,
with focus on Legacy Computing symbols, connective scripts, and symbols.

Controls:
    UP/DOWN or J/K: Navigate sections
    ESC: Exit
"""

import sys
sys.path.insert(0, 'src')

import pyunicodegame
import pygame

# Demo sections with characters and descriptions
SECTIONS = [
    {
        "title": "Symbols for Legacy Computing (U+1FB00-U+1FBFF)",
        "subtitle": "Block sextants for high-resolution text graphics",
        "color": (100, 200, 255),
        "rows": [
            ("Block Sextants", [chr(0x1FB00 + i) for i in range(24)]),
            ("More Sextants", [chr(0x1FB00 + i) for i in range(24, 48)]),
            ("Wedges", [chr(0x1FB3C + i) for i in range(20)]),
            ("Octants", [chr(0x1FB82 + i) for i in range(12)]),
            ("Patterns", [chr(0x1FB95), chr(0x1FB96), chr(0x1FB97), chr(0x1FB98), chr(0x1FB99)] +
                        [chr(0x1FB9A + i) for i in range(6)]),
        ]
    },
    {
        "title": "Legacy Computing Supplement (U+1CC00-U+1CEFF)",
        "subtitle": "Additional block graphics from Unicode 16.0 (2024)",
        "color": (100, 255, 200),
        "rows": [
            ("Octant Row 1", [chr(0x1CC00 + i) for i in range(24)]),
            ("Octant Row 2", [chr(0x1CC18 + i) for i in range(24)]),
            ("Octant Row 3", [chr(0x1CC30 + i) for i in range(24)]),
            ("Octant Row 4", [chr(0x1CC48 + i) for i in range(24)]),
            ("Octant Row 5", [chr(0x1CC60 + i) for i in range(24)]),
        ]
    },
    {
        "title": "Box Drawing & Block Elements",
        "subtitle": "Classic terminal graphics characters",
        "color": (255, 200, 100),
        "rows": [
            ("Light Box", list("┌─┬─┐│ │ │├─┼─┤└─┴─┘")),
            ("Heavy Box", list("┏━┳━┓┃ ┃ ┃┣━╋━┫┗━┻━┛")),
            ("Double Box", list("╔═╦═╗║ ║ ║╠═╬═╣╚═╩═╝")),
            ("Blocks", [chr(0x2580 + i) for i in range(16)] + [chr(0x2590 + i) for i in range(16)]),
            ("Shades", list("░░▒▒▓▓██") + ["  "] + list("▀▄█▌▐")),
        ]
    },
    {
        "title": "Arabic Script (U+0600-U+06FF)",
        "subtitle": "Right-to-left connective script",
        "color": (150, 255, 150),
        "rows": [
            ("Letters", list("ابتثجحخدذرزسشصضطظعغفقكلمنهوي")),
            ("With marks", list("أإآؤئءًٌٍَُِّْ")),
            ("Sample", list("السلام عليكم")),
        ]
    },
    {
        "title": "Hebrew Script (U+0590-U+05FF)",
        "subtitle": "Right-to-left Semitic script",
        "color": (200, 150, 255),
        "rows": [
            ("Letters", list("אבגדהוזחטיכלמנסעפצקרשת")),
            ("Final forms", list("ךםןףץ")),
            ("Sample", list("שלום עולם")),
        ]
    },
    {
        "title": "Devanagari Script (U+0900-U+097F)",
        "subtitle": "Used for Hindi, Sanskrit, and many Indian languages",
        "color": (255, 150, 200),
        "rows": [
            ("Vowels", list("अआइईउऊऋएऐओऔ")),
            ("Consonants", list("कखगघङचछजझञटठडढण")),
            ("More cons.", list("तथदधनपफबभमयरलवशषसह")),
            ("Sample", list("नमस्ते")),
        ]
    },
    {
        "title": "Braille Patterns (U+2800-U+28FF)",
        "subtitle": "All 256 braille dot combinations",
        "color": (255, 255, 150),
        "rows": [
            ("Row 1", [chr(0x2800 + i) for i in range(32)]),
            ("Row 2", [chr(0x2800 + i) for i in range(32, 64)]),
            ("Row 3", [chr(0x2800 + i) for i in range(64, 96)]),
            ("Row 4", [chr(0x2800 + i) for i in range(96, 128)]),
        ]
    },
    {
        "title": "Animal Emoji (U+1F400+)",
        "subtitle": "Pixel art animals - frog, turtle, and friends",
        "color": (255, 200, 150),
        "rows": [
            ("Mammals", list("🐀🐁🐂🐃🐄🐅🐆🐇🐈🐕🐖🐘🐪🐫")),
            ("More mammals", list("🐭🐮🐯🐰🐱🐴🐵🐶🐷🐹🐺🐻🐼🦁")),
            ("Sea life", list("🐊🐋🐙🐚🐟🐠🐡🐢🐬🐳🦀🦈")),
            ("Birds", list("🐓🐔🐣🐤🐥🐦🐧🦃🦅🦆🦉")),
            ("Bugs & more", list("🐌🐍🐛🐜🐝🐞🕷🦂🦋🦎🐸")),
        ]
    },
    {
        "title": "Emoticons & Weather (U+1F600+)",
        "subtitle": "Faces and weather symbols",
        "color": (255, 220, 180),
        "rows": [
            ("Faces", [chr(0x1F600 + i) for i in range(16)]),
            ("More faces", [chr(0x1F610 + i) for i in range(16)]),
            ("Weather", [chr(0x1F300 + i) for i in range(16)]),
        ]
    },
    {
        "title": "Musical Symbols (U+1D100-U+1D1FF)",
        "subtitle": "Western musical notation",
        "color": (200, 255, 200),
        "rows": [
            ("Notes", [chr(0x1D100 + i) for i in range(20)]),
            ("More", [chr(0x1D100 + i) for i in range(20, 40)]),
            ("Clefs etc", [chr(0x1D11E), chr(0x1D11F), chr(0x1D120), chr(0x1D121), chr(0x1D122)]),
        ]
    },
    {
        "title": "Games: Mahjong, Cards, Dominos",
        "subtitle": "Game piece symbols",
        "color": (255, 180, 180),
        "rows": [
            ("Mahjong", [chr(0x1F000 + i) for i in range(24)]),
            ("Cards", [chr(0x1F0A1 + i) for i in range(14)]),  # Spades
            ("Dominos", [chr(0x1F030 + i) for i in range(20)]),
        ]
    },
    {
        "title": "Dingbats & Symbols (U+2700+)",
        "subtitle": "Decorative symbols and ornaments",
        "color": (180, 220, 255),
        "rows": [
            ("Dingbats", [chr(0x2700 + i) for i in range(24)]),
            ("More", [chr(0x2718 + i) for i in range(24)]),
            ("Arrows", list("←↑→↓↔↕↖↗↘↙⇐⇑⇒⇓⇔⇕")),
            ("Stars", list("★☆✦✧✩✪✫✬✭✮✯✰")),
        ]
    },
    {
        "title": "Geometric Shapes (U+25A0-U+25FF)",
        "subtitle": "Basic geometric forms",
        "color": (220, 180, 255),
        "rows": [
            ("Squares", list("■□▢▣▤▥▦▧▨▩")),
            ("Circles", list("●○◐◑◒◓◔◕◖◗")),
            ("Triangles", list("▲△▴▵▶▷▸▹►▻")),
            ("Diamonds", list("◆◇◈◊⬥⬦⬧⬨")),
        ]
    },
    {
        "title": "Miscellaneous Symbols (U+2600-U+26FF)",
        "subtitle": "Weather, astrology, games, and more",
        "color": (255, 220, 180),
        "rows": [
            ("Weather", list("☀☁☂☃☄★☆☇☈")),
            ("Zodiac", list("♈♉♊♋♌♍♎♏♐♑♒♓")),
            ("Chess", list("♔♕♖♗♘♙♚♛♜♝♞♟")),
            ("Cards", list("♠♡♢♣♤♥♦♧")),
            ("Music", list("♩♪♫♬♭♮♯")),
        ]
    },
]

current_section = 0


def render():
    root = pyunicodegame.get_window("root")
    section = SECTIONS[current_section]

    # Header
    root.put_string(2, 1, f"GNU Unifont Demo ({current_section + 1}/{len(SECTIONS)})", (255, 255, 255))
    root.put_string(2, 2, "─" * 56, (80, 80, 80))

    # Section title
    root.put_string(2, 4, section["title"], section["color"])
    root.put_string(2, 5, section["subtitle"], (150, 150, 150))

    # Character rows
    y = 7
    for label, chars in section["rows"]:
        if y >= 23:
            break
        # Label
        root.put_string(2, y, f"{label}:", (180, 180, 180))
        # Characters (start after longest label + padding)
        char_str = "".join(chars)
        root.put_string(18, y, char_str, section["color"])
        y += 1

    # Footer
    root.put_string(2, 25, "↑/↓ or J/K: Navigate   ESC: Exit", (100, 100, 100))

    # Navigation hint
    nav_text = ""
    if current_section > 0:
        nav_text += f"← {SECTIONS[current_section - 1]['title'][:20]}..."
    if current_section < len(SECTIONS) - 1:
        if nav_text:
            nav_text += "  "
        nav_text += f"→ {SECTIONS[current_section + 1]['title'][:20]}..."
    root.put_string(2, 26, nav_text, (80, 80, 80))


def on_key(key):
    global current_section

    if key in (pygame.K_UP, pygame.K_k):
        current_section = (current_section - 1) % len(SECTIONS)
    elif key in (pygame.K_DOWN, pygame.K_j):
        current_section = (current_section + 1) % len(SECTIONS)


def main():
    pyunicodegame.init(
        "GNU Unifont Character Demo",
        width=60,
        height=28,
        font_name="unifont",
        bg=(15, 15, 25, 255)
    )

    pyunicodegame.run(render=render, on_key=on_key)


if __name__ == "__main__":
    main()
