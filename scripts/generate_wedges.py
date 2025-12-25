#!/usr/bin/env python3
"""
Generate Legacy Computing wedge characters (U+1FB3C-U+1FB67) for BDF fonts.

Usage:
    python generate_wedges.py -W 10 -H 20 -o wedges.bdf
    python generate_wedges.py -f existing.bdf -o wedges.bdf
    python generate_wedges.py --add-to font.bdf --replace
    python generate_wedges.py --preview
"""

import argparse
import re
import sys


# Define edge points as fractions of cell dimensions
# Format: (x_fraction, y_fraction) where (0,0) is top-left, (1,1) is bottom-right
# "1/3" and "2/3" refer to position from BOTTOM, so:
#   left_1_3 = 1/3 up from bottom = y=2/3 in top-down coords
#   left_2_3 = 2/3 up from bottom = y=1/3 in top-down coords
POINTS = {
    'TL': (0, 0),
    'TR': (1, 0),
    'BL': (0, 1),
    'BR': (1, 1),
    'top_mid': (0.5, 0),
    'bot_mid': (0.5, 1),
    'left_1_3': (0, 2/3),   # 1/3 up from bottom
    'left_2_3': (0, 1/3),   # 2/3 up from bottom
    'right_1_3': (1, 2/3),  # 1/3 up from bottom
    'right_2_3': (1, 1/3),  # 2/3 up from bottom
}

# The 22 base wedge shapes, defined by (point_a, point_b)
# Each fills the region where cross-product of line vector and point is >= 0
WEDGE_DEFINITIONS = [
    ('left_1_3', 'bot_mid'),    # 1FB3C
    ('left_1_3', 'BR'),          # 1FB3D
    ('left_2_3', 'bot_mid'),    # 1FB3E
    ('left_2_3', 'BR'),          # 1FB3F
    ('TL', 'bot_mid'),           # 1FB40
    ('left_2_3', 'top_mid'),    # 1FB41
    ('left_2_3', 'TR'),          # 1FB42
    ('left_1_3', 'top_mid'),    # 1FB43
    ('left_1_3', 'TR'),          # 1FB44
    ('BL', 'top_mid'),           # 1FB45
    ('left_1_3', 'right_2_3'),  # 1FB46
    ('bot_mid', 'right_1_3'),   # 1FB47
    ('BL', 'right_1_3'),         # 1FB48
    ('bot_mid', 'right_2_3'),   # 1FB49
    ('BL', 'right_2_3'),         # 1FB4A
    ('bot_mid', 'TR'),           # 1FB4B
    ('top_mid', 'right_2_3'),   # 1FB4C
    ('TL', 'right_2_3'),         # 1FB4D
    ('top_mid', 'right_1_3'),   # 1FB4E
    ('TL', 'right_1_3'),         # 1FB4F
    ('top_mid', 'BR'),           # 1FB50
    ('left_2_3', 'right_1_3'),  # 1FB51
]

# Starting codepoint
BASE_CODEPOINT = 0x1FB3C


def point_side_of_line(px, py, x1, y1, x2, y2):
    """
    Determine which side of a line a point is on.
    Returns positive if point is on the left/above side of line from (x1,y1) to (x2,y2),
    negative if on right/below side, 0 if on the line.
    """
    return (x2 - x1) * (py - y1) - (y2 - y1) * (px - x1)


def generate_wedge_bitmap(width, height, point_a, point_b):
    """
    Generate a bitmap for a wedge shape.

    Args:
        width: Cell width in pixels
        height: Cell height in pixels
        point_a: Name of first point defining the diagonal
        point_b: Name of second point defining the diagonal

    Returns:
        List of integers, one per row, representing the bitmap
    """
    # Get actual coordinates
    ax, ay = POINTS[point_a]
    bx, by = POINTS[point_b]

    # Convert to pixel coordinates (use cell boundaries)
    x1 = ax * width
    y1 = ay * height
    x2 = bx * width
    y2 = by * height

    bitmap = []

    for row in range(height):
        row_bits = 0
        for col in range(width):
            # Test center of pixel
            px = col + 0.5
            py = row + 0.5

            side = point_side_of_line(px, py, x1, y1, x2, y2)

            # Fill where cross-product is non-negative
            if side >= 0:
                row_bits |= (1 << (width - 1 - col))

        bitmap.append(row_bits)

    return bitmap


def invert_bitmap(bitmap, width):
    """Invert a bitmap (swap filled and empty pixels)."""
    mask = (1 << width) - 1
    return [mask ^ row for row in bitmap]


def bitmap_to_hex(bitmap, width):
    """Convert bitmap to hex strings for BDF format."""
    # BDF uses byte-aligned rows, padded to the right
    bytes_per_row = (width + 7) // 8
    hex_lines = []

    for row in bitmap:
        # Shift to align to byte boundary (pad on right)
        shift = bytes_per_row * 8 - width
        padded = row << shift
        hex_str = format(padded, f'0{bytes_per_row * 2}X')
        hex_lines.append(hex_str)

    return hex_lines


def generate_bdf_glyph(codepoint, bitmap, width, height, descent=0, name=None):
    """Generate BDF glyph entry."""
    if name is None:
        name = f"U{codepoint:04X}"

    hex_lines = bitmap_to_hex(bitmap, width)

    lines = [
        f"STARTCHAR {name}",
        f"ENCODING {codepoint}",
        f"SWIDTH {width * 48} 0",
        f"DWIDTH {width} 0",
        f"BBX {width} {height} 0 {-descent}",
        "BITMAP",
    ]
    lines.extend(hex_lines)
    lines.append("ENDCHAR")

    return '\n'.join(lines)


def generate_all_wedges(width, height, descent=0):
    """Generate all 44 wedge characters (22 base + 22 inverted)."""
    glyphs = []
    codepoint = BASE_CODEPOINT

    # Generate 22 base wedges
    for point_a, point_b in WEDGE_DEFINITIONS:
        bitmap = generate_wedge_bitmap(width, height, point_a, point_b)
        glyph = generate_bdf_glyph(codepoint, bitmap, width, height, descent)
        glyphs.append(glyph)
        codepoint += 1

    # Generate 22 inverted wedges
    for point_a, point_b in WEDGE_DEFINITIONS:
        bitmap = generate_wedge_bitmap(width, height, point_a, point_b)
        inverted = invert_bitmap(bitmap, width)
        glyph = generate_bdf_glyph(codepoint, inverted, width, height, descent)
        glyphs.append(glyph)
        codepoint += 1

    return glyphs


def generate_bdf_file(width, height, descent=0, font_name=None):
    """Generate complete BDF file content."""
    if font_name is None:
        font_name = f"LegacyWedges-{width}x{height}"

    glyphs = generate_all_wedges(width, height, descent)

    header = f"""STARTFONT 2.1
FONT -{font_name}-Medium-R-Normal--{height}-{height*10}-75-75-C-{width*10}-ISO10646-1
SIZE {height} 75 75
FONTBOUNDINGBOX {width} {height} 0 0
STARTPROPERTIES 2
FONT_ASCENT {height}
FONT_DESCENT 0
ENDPROPERTIES
CHARS {len(glyphs)}
"""

    footer = "\nENDFONT\n"

    return header + '\n'.join(glyphs) + footer


def preview_wedge(width, height, point_a, point_b):
    """Print ASCII preview of a wedge."""
    bitmap = generate_wedge_bitmap(width, height, point_a, point_b)
    print(f"\n{point_a} -> {point_b}:")
    for row in bitmap:
        bits = format(row, f'0{width}b')
        print(bits.replace('0', '·').replace('1', '█'))


def get_font_metrics(bdf_path):
    """Extract width, height, and descent from a BDF font file."""
    with open(bdf_path, 'r') as f:
        content = f.read()

    match = re.search(r'FONTBOUNDINGBOX\s+(\d+)\s+(\d+)\s+(-?\d+)\s+(-?\d+)', content)
    if not match:
        raise ValueError("Could not find FONTBOUNDINGBOX in font")

    width = int(match.group(1))
    height = int(match.group(2))
    y_offset = int(match.group(4))
    descent = -y_offset

    return width, height, descent


def main():
    parser = argparse.ArgumentParser(description='Generate Legacy Computing wedge characters')
    parser.add_argument('-W', '--width', type=int, help='Cell width in pixels')
    parser.add_argument('-H', '--height', type=int, help='Cell height in pixels')
    parser.add_argument('-d', '--descent', type=int, default=0, help='Font descent in pixels (e.g., 4 for 10x20)')
    parser.add_argument('-f', '--font', type=str, help='Read metrics from existing BDF font')
    parser.add_argument('-o', '--output', type=str, help='Output BDF file path')
    parser.add_argument('--add-to', nargs='+', metavar='FONT', help='Add/replace wedges in existing BDF font(s)')
    parser.add_argument('--replace', action='store_true', help='Replace existing wedge characters (with --add-to)')
    parser.add_argument('--preview', action='store_true', help='Preview wedges in terminal')
    parser.add_argument('--preview-index', type=int, help='Preview specific wedge (0-21)')

    args = parser.parse_args()

    # Handle --add-to mode
    if args.add_to:
        for font_path in args.add_to:
            add_to_font(font_path, args.replace)
        return

    # Get dimensions from font file or arguments
    if args.font:
        width, height, descent = get_font_metrics(args.font)
        print(f"Read from {args.font}: {width}x{height}, descent={descent}", file=sys.stderr)
    else:
        width = args.width or 10
        height = args.height or 20
        descent = args.descent

    if args.preview:
        print(f"Previewing wedges at {width}x{height}:")
        for i, (pa, pb) in enumerate(WEDGE_DEFINITIONS):
            if args.preview_index is None or args.preview_index == i:
                print(f"\n[{i}] U+{BASE_CODEPOINT + i:04X}:", end='')
                preview_wedge(width, height, pa, pb)
        return

    bdf_content = generate_bdf_file(width, height, descent)

    if args.output:
        with open(args.output, 'w') as f:
            f.write(bdf_content)
        print(f"Generated {args.output} ({width}x{height}, 44 glyphs)")
    else:
        print(bdf_content)


def add_to_font(bdf_path, replace=False):
    """Add or replace wedge characters in an existing BDF font."""
    width, height, descent = get_font_metrics(bdf_path)
    print(f"{bdf_path}: {width}x{height}, descent={descent}")

    with open(bdf_path, 'r') as f:
        content = f.read()

    # Check if wedges already exist
    has_wedges = 'ENCODING 129852' in content

    if has_wedges and not replace:
        print("  Wedge characters already exist. Use --replace to replace them.")
        return

    if has_wedges:
        # Remove existing wedge chars (U+1FB3C to U+1FB67 = 129852 to 129895)
        for cp in range(129852, 129896):
            pattern = rf'STARTCHAR [^\n]*\nENCODING {cp}\n.*?ENDCHAR\n'
            content = re.sub(pattern, '', content, flags=re.DOTALL)
        print("  Removed existing wedge characters")

    # Generate new wedges with correct descent
    glyphs = generate_all_wedges(width, height, descent)
    wedge_content = '\n'.join(glyphs) + '\n'

    # Insert before ENDFONT
    content = content.replace('ENDFONT', wedge_content + 'ENDFONT')

    # Update CHARS count if adding (not replacing)
    if not has_wedges:
        match = re.search(r'^CHARS\s+(\d+)', content, re.MULTILINE)
        old_count = int(match.group(1))
        content = re.sub(r'^CHARS\s+\d+', f'CHARS {old_count + 44}', content, flags=re.MULTILINE)

    with open(bdf_path, 'w') as f:
        f.write(content)

    action = "Replaced" if has_wedges else "Added"
    print(f"  {action} 44 wedge characters")


if __name__ == '__main__':
    main()
