#!/usr/bin/env python3
"""
Convert BDF bitmap font to TTF by tracing pixels into vector outlines.

Usage:
    python bdf_to_ttf.py input.bdf output.ttf
    python bdf_to_ttf.py  # Uses default 10x20.bdf -> Pyunicodegame10x20.ttf

Requirements:
    pip install fonttools bdflib
"""

import argparse
import os
import sys

from bdflib import reader
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen


def parse_bdf(bdf_path):
    """Parse BDF file and return font info and glyphs."""
    with open(bdf_path, 'rb') as f:
        font = reader.read_bdf(f)

    glyphs = {}
    for glyph in font.glyphs:
        if glyph.codepoint >= 0:
            glyphs[glyph.codepoint] = {
                'width': glyph.advance,
                'bitmap': glyph.data,
                'bbW': glyph.bbW,
                'bbH': glyph.bbH,
                'bbX': glyph.bbX,
                'bbY': glyph.bbY,
            }

    ascent = font.properties.get(b'FONT_ASCENT', 16)
    descent = font.properties.get(b'FONT_DESCENT', 4)

    return {'ascent': ascent, 'descent': descent, 'glyphs': glyphs}


def draw_bitmap_glyph(pen, bitmap, bbW, bbH, bbX, bbY, scale):
    """Draw bitmap as rectangles.

    Note: bdflib returns rows in REVERSE order (index 0 = bottom row)
    and values are right-aligned integers for the glyph width.
    """
    for row_idx, row in enumerate(bitmap):
        for col in range(bbW):
            # bdflib right-aligns values, so bit (bbW-1-col) is column 'col' from left
            if row & (1 << (bbW - 1 - col)):
                # X position: column offset from bbox origin
                x = int((bbX + col) * scale)
                # Y position: bdflib row 0 is BOTTOM, so y = bbY + row_idx
                y = int((bbY + row_idx) * scale)
                w = int(scale)
                h = int(scale)

                # Draw rectangle counter-clockwise
                pen.moveTo((x, y))
                pen.lineTo((x, y + h))
                pen.lineTo((x + w, y + h))
                pen.lineTo((x + w, y))
                pen.closePath()


def create_ttf_from_bdf(bdf_path, ttf_path, family_name=None):
    """Create TTF from BDF with outlined glyphs."""
    font_info = parse_bdf(bdf_path)

    if family_name is None:
        # Derive from filename
        basename = os.path.splitext(os.path.basename(bdf_path))[0]
        family_name = f"Pyunicodegame {basename}"

    units_per_em = 1000
    cell_height = font_info['ascent'] + font_info['descent']
    scale = units_per_em / cell_height

    ascent = int(font_info['ascent'] * scale)
    descent = int(font_info['descent'] * scale)

    # Build glyph order
    glyph_order = ['.notdef']
    cmap = {}

    for cp in sorted(font_info['glyphs'].keys()):
        glyph_order.append(f"uni{cp:04X}")
        cmap[cp] = f"uni{cp:04X}"

    fb = FontBuilder(units_per_em, isTTF=True)
    fb.setupGlyphOrder(glyph_order)

    # Get cell width from first glyph (all should be same for monospace)
    first_glyph = next(iter(font_info['glyphs'].values()))
    cell_width = first_glyph['width']

    pen_glyphs = {}
    metrics = {}  # (advance_width, lsb) per glyph

    # Empty .notdef glyph
    pen = TTGlyphPen(None)
    pen_glyphs['.notdef'] = pen.glyph()
    metrics['.notdef'] = (int(cell_width * scale), 0)

    # Process each glyph
    count = 0
    for cp, g in font_info['glyphs'].items():
        name = f"uni{cp:04X}"
        pen = TTGlyphPen(None)

        if g['bitmap'] and any(row != 0 for row in g['bitmap']):
            draw_bitmap_glyph(
                pen, g['bitmap'],
                g['bbW'], g['bbH'], g['bbX'], g['bbY'],
                scale
            )

        glyph = pen.glyph()
        glyph.recalcBounds(None)  # Calculate xMin/xMax
        pen_glyphs[name] = glyph
        advance = int(g['width'] * scale)
        # LSB should be the glyph's xMin (0 for empty glyphs)
        lsb = glyph.xMin if glyph.numberOfContours else 0
        metrics[name] = (advance, lsb)
        count += 1

        if count % 1000 == 0:
            print(f"Processed {count} glyphs...")

    print(f"Total: {count} glyphs")

    # Setup font tables
    fb.setupGlyf(pen_glyphs)
    fb.setupCharacterMap(cmap)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=ascent, descent=-descent)

    # Clean family name for PostScript (no spaces)
    ps_name = family_name.replace(' ', '')

    fb.setupNameTable({
        'familyName': family_name,
        'styleName': 'Regular',
        'uniqueFontIdentifier': f'{ps_name}-Regular',
        'fullName': f'{family_name} Regular',
        'version': 'Version 1.0',
        'psName': f'{ps_name}-Regular',
    })

    fb.setupOS2(
        sTypoAscender=ascent,
        sTypoDescender=-descent,
        sTypoLineGap=0,
        usWinAscent=ascent,
        usWinDescent=descent,
        sxHeight=int(ascent * 0.5),
        sCapHeight=ascent,
    )

    fb.setupPost(isFixedPitch=True)
    fb.setupHead(unitsPerEm=units_per_em)

    fb.save(ttf_path)
    print(f"Saved to {ttf_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Convert BDF bitmap font to TTF with vector outlines'
    )
    parser.add_argument(
        'input', nargs='?',
        default='../src/pyunicodegame/fonts/10x20.bdf',
        help='Input BDF file (default: ../src/pyunicodegame/fonts/10x20.bdf)'
    )
    parser.add_argument(
        'output', nargs='?',
        help='Output TTF file (default: derived from input name)'
    )
    parser.add_argument(
        '--name', '-n',
        help='Font family name (default: derived from filename)'
    )

    args = parser.parse_args()

    # Handle relative paths from script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = args.input
    if not os.path.isabs(input_path):
        input_path = os.path.join(script_dir, input_path)

    if not os.path.exists(input_path):
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    # Derive output path if not specified
    if args.output:
        output_path = args.output
    else:
        basename = os.path.splitext(os.path.basename(input_path))[0]
        output_path = os.path.join(script_dir, f'Pyunicodegame{basename}.ttf')

    create_ttf_from_bdf(input_path, output_path, args.name)


if __name__ == '__main__':
    main()
