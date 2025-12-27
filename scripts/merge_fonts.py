#!/usr/bin/env python3
"""Merge missing characters from Unifont hex into UnifontEX BDF."""

import sys

def hex_to_bdf_char(codepoint_hex: str, bitmap_hex: str) -> str:
    """Convert a Unifont hex entry to BDF character format."""
    # Parse codepoint (remove leading zeros)
    codepoint = int(codepoint_hex, 16)

    # Determine width from bitmap length
    # 32 hex chars = 8px wide (16 bytes), 64 hex chars = 16px wide (32 bytes)
    if len(bitmap_hex) == 32:
        width = 8
        swidth = 500
        bytes_per_row = 1
    elif len(bitmap_hex) == 64:
        width = 16
        swidth = 1000
        bytes_per_row = 2
    else:
        print(f"Warning: Unknown bitmap length {len(bitmap_hex)} for U+{codepoint_hex}", file=sys.stderr)
        return ""

    # Build BDF character entry
    lines = [
        f"STARTCHAR uni{codepoint:04X}",
        f"ENCODING {codepoint}",
        f"SWIDTH {swidth} 0",
        f"DWIDTH {width} 0",
        f"BBX {width} 16 0 -2",
        "BITMAP",
    ]

    # Split bitmap into rows (2 or 4 hex chars per row)
    chars_per_row = bytes_per_row * 2
    for i in range(0, len(bitmap_hex), chars_per_row):
        row = bitmap_hex[i:i+chars_per_row]
        lines.append(row.upper())

    lines.append("ENDCHAR")
    return "\n".join(lines)


def get_existing_encodings(bdf_path: str) -> set:
    """Extract all ENCODING values from a BDF file."""
    encodings = set()
    with open(bdf_path, 'r') as f:
        for line in f:
            if line.startswith("ENCODING "):
                try:
                    enc = int(line.split()[1])
                    if enc >= 0:  # Skip -1 (notdef)
                        encodings.add(enc)
                except (ValueError, IndexError):
                    pass
    return encodings


def parse_hex_file(hex_path: str) -> dict:
    """Parse Unifont hex file into {codepoint: bitmap} dict."""
    chars = {}
    with open(hex_path, 'r') as f:
        for line in f:
            line = line.strip()
            if ':' in line:
                parts = line.split(':')
                if len(parts) == 2:
                    codepoint_hex = parts[0].lstrip('0') or '0'
                    bitmap_hex = parts[1]
                    codepoint = int(codepoint_hex, 16)
                    chars[codepoint] = (codepoint_hex, bitmap_hex)
    return chars


def main():
    unifontex_bdf = "/Users/henry/Documents/github/pygame/src/pyunicodegame/fonts/unifontex.bdf"
    unifont_upper_hex = "/tmp/unifont_upper.hex"

    print("Loading existing UnifontEX encodings...")
    existing = get_existing_encodings(unifontex_bdf)
    print(f"  Found {len(existing)} existing characters")

    print("Loading Unifont upper plane characters...")
    upper_chars = parse_hex_file(unifont_upper_hex)
    print(f"  Found {len(upper_chars)} upper plane characters")

    # Find missing characters
    missing = {cp: data for cp, data in upper_chars.items() if cp not in existing}
    print(f"  {len(missing)} characters missing from UnifontEX")

    if not missing:
        print("No characters to add!")
        return

    # Read existing BDF
    print("Reading UnifontEX BDF...")
    with open(unifontex_bdf, 'r') as f:
        bdf_content = f.read()

    # Find CHARS count and update it
    import re
    chars_match = re.search(r'^CHARS (\d+)', bdf_content, re.MULTILINE)
    if chars_match:
        old_count = int(chars_match.group(1))
        new_count = old_count + len(missing)
        bdf_content = bdf_content.replace(f"CHARS {old_count}", f"CHARS {new_count}", 1)
        print(f"  Updated CHARS: {old_count} -> {new_count}")

    # Find position before ENDFONT to insert new characters
    endfont_pos = bdf_content.rfind("ENDFONT")
    if endfont_pos == -1:
        print("ERROR: Could not find ENDFONT in BDF")
        return

    # Generate BDF entries for missing characters
    print("Converting missing characters to BDF format...")
    new_entries = []
    for codepoint in sorted(missing.keys()):
        codepoint_hex, bitmap_hex = missing[codepoint]
        entry = hex_to_bdf_char(codepoint_hex, bitmap_hex)
        if entry:
            new_entries.append(entry)

    # Insert new characters before ENDFONT
    new_bdf = bdf_content[:endfont_pos] + "\n".join(new_entries) + "\n" + bdf_content[endfont_pos:]

    # Write merged BDF
    print("Writing merged BDF...")
    with open(unifontex_bdf, 'w') as f:
        f.write(new_bdf)

    print(f"\nDone! Added {len(new_entries)} characters to UnifontEX")

    # Show some stats about what was added
    legacy_computing = [cp for cp in missing.keys() if 0x1FB00 <= cp <= 0x1FBFF]
    print(f"  Including {len(legacy_computing)} Symbols for Legacy Computing (U+1FB00-U+1FBFF)")


if __name__ == "__main__":
    main()
