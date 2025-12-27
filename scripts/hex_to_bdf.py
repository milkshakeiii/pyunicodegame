#!/usr/bin/env python3
"""Convert Unifont .hex files to BDF format."""

import argparse
import sys


def hex_to_bdf(hex_path: str, output_path: str, font_name: str = "Unifont"):
    """Convert Unifont hex file to BDF format."""

    # Parse hex file
    chars = []
    with open(hex_path, 'r') as f:
        for line in f:
            line = line.strip()
            if ':' in line:
                parts = line.split(':')
                if len(parts) == 2:
                    codepoint = int(parts[0], 16)
                    bitmap_hex = parts[1]
                    chars.append((codepoint, bitmap_hex))

    chars.sort(key=lambda x: x[0])
    print(f"Parsed {len(chars)} characters from {hex_path}")

    # Write BDF header
    with open(output_path, 'w') as f:
        f.write(f"""STARTFONT 2.1
FONT -{font_name}-Medium-R-Normal--16-160-75-75-C-80-ISO10646-1
SIZE 16 75 75
FONTBOUNDINGBOX 16 16 0 -2
STARTPROPERTIES 4
FONT_ASCENT 14
FONT_DESCENT 2
DEFAULT_CHAR 0
SPACING "C"
ENDPROPERTIES
CHARS {len(chars)}
""")

        # Write each character
        for codepoint, bitmap_hex in chars:
            # Determine width from bitmap length
            if len(bitmap_hex) == 32:
                width = 8
                swidth = 500
                bytes_per_row = 1
            elif len(bitmap_hex) == 64:
                width = 16
                swidth = 1000
                bytes_per_row = 2
            else:
                print(f"Warning: Unknown bitmap length {len(bitmap_hex)} for U+{codepoint:04X}", file=sys.stderr)
                continue

            f.write(f"STARTCHAR uni{codepoint:04X}\n")
            f.write(f"ENCODING {codepoint}\n")
            f.write(f"SWIDTH {swidth} 0\n")
            f.write(f"DWIDTH {width} 0\n")
            f.write(f"BBX {width} 16 0 -2\n")
            f.write("BITMAP\n")

            # Split bitmap into rows
            chars_per_row = bytes_per_row * 2
            for i in range(0, len(bitmap_hex), chars_per_row):
                row = bitmap_hex[i:i+chars_per_row]
                f.write(row.upper() + "\n")

            f.write("ENDCHAR\n")

        f.write("ENDFONT\n")

    print(f"Wrote {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Convert Unifont .hex to BDF')
    parser.add_argument('hex_file', help='Input .hex file')
    parser.add_argument('bdf_file', help='Output .bdf file')
    parser.add_argument('--name', default='Unifont', help='Font name (default: Unifont)')
    args = parser.parse_args()

    hex_to_bdf(args.hex_file, args.bdf_file, args.name)


if __name__ == "__main__":
    main()
