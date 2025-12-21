"""
pyunicodegame.ui.text - Text wrapping and alignment utilities.

QUICK START:
    from pyunicodegame.ui.text import wrap_text, align_text

    lines = wrap_text("A long string that needs wrapping", width=20)
    centered = align_text("Title", width=30, align="center")

FUNCTIONS:
    wrap_text(text, width) - Wrap text to fit within a width
    align_text(text, width, align) - Align text within a width
    truncate(text, width, suffix) - Truncate text with suffix
"""

from typing import List


def wrap_text(
    text: str,
    width: int,
    preserve_newlines: bool = True,
) -> List[str]:
    """
    Wrap text to fit within a specified width.

    Words are kept whole when possible. Very long words that exceed
    the width are broken.

    Args:
        text: The text to wrap
        width: Maximum line width in characters
        preserve_newlines: If True, existing newlines are preserved

    Returns:
        List of wrapped lines

    Example:
        >>> wrap_text("The quick brown fox jumps", width=10)
        ['The quick', 'brown fox', 'jumps']
    """
    if width <= 0:
        return []

    result = []

    # Split on newlines if preserving them
    if preserve_newlines:
        paragraphs = text.split("\n")
    else:
        paragraphs = [text.replace("\n", " ")]

    for paragraph in paragraphs:
        if not paragraph:
            result.append("")
            continue

        words = paragraph.split()
        if not words:
            result.append("")
            continue

        current_line = []
        current_length = 0

        for word in words:
            word_len = len(word)

            # Word fits on current line
            if current_length + word_len + (1 if current_line else 0) <= width:
                current_line.append(word)
                current_length += word_len + (1 if current_length > 0 else 0)

            # Word doesn't fit but line has content - start new line
            elif current_line:
                result.append(" ".join(current_line))
                current_line = []
                current_length = 0

                # Handle very long words
                if word_len > width:
                    while len(word) > width:
                        result.append(word[:width])
                        word = word[width:]
                    if word:
                        current_line = [word]
                        current_length = len(word)
                else:
                    current_line = [word]
                    current_length = word_len

            # First word on line but too long
            else:
                while len(word) > width:
                    result.append(word[:width])
                    word = word[width:]
                if word:
                    current_line = [word]
                    current_length = len(word)

        # Don't forget the last line
        if current_line:
            result.append(" ".join(current_line))

    return result


def align_text(
    text: str,
    width: int,
    align: str = "left",
    fill_char: str = " ",
) -> str:
    """
    Align text within a specified width.

    Args:
        text: The text to align
        width: Total width to fit within
        align: Alignment mode - "left", "right", or "center"
        fill_char: Character to use for padding

    Returns:
        Aligned text string

    Example:
        >>> align_text("Hello", 10, "center")
        '  Hello   '
        >>> align_text("Hello", 10, "right")
        '     Hello'
    """
    text_len = len(text)

    if text_len >= width:
        return text[:width]

    padding = width - text_len

    if align == "left":
        return text + fill_char * padding
    elif align == "right":
        return fill_char * padding + text
    elif align == "center":
        left_pad = padding // 2
        right_pad = padding - left_pad
        return fill_char * left_pad + text + fill_char * right_pad
    else:
        return text + fill_char * padding


def truncate(
    text: str,
    width: int,
    suffix: str = "\u2026",  # Ellipsis
) -> str:
    """
    Truncate text to fit within a width, adding a suffix if truncated.

    Args:
        text: The text to truncate
        width: Maximum width
        suffix: String to append when truncated (default: ellipsis)

    Returns:
        Truncated text

    Example:
        >>> truncate("Hello World", 8)
        'Hello W\u2026'
    """
    if len(text) <= width:
        return text

    if width <= len(suffix):
        return suffix[:width]

    return text[:width - len(suffix)] + suffix


def pad_lines(
    lines: List[str],
    width: int,
    align: str = "left",
    fill_char: str = " ",
) -> List[str]:
    """
    Pad all lines to a consistent width.

    Args:
        lines: List of text lines
        width: Target width for all lines
        align: Alignment mode
        fill_char: Padding character

    Returns:
        List of padded lines
    """
    return [align_text(line, width, align, fill_char) for line in lines]


def columnize(
    items: List[str],
    width: int,
    columns: int = 2,
    gap: int = 2,
) -> List[str]:
    """
    Arrange items into columns.

    Args:
        items: List of items to arrange
        width: Total width available
        columns: Number of columns
        gap: Gap between columns

    Returns:
        List of lines with columnar layout
    """
    if not items or columns <= 0:
        return []

    # Calculate column width
    col_width = (width - gap * (columns - 1)) // columns

    result = []
    for i in range(0, len(items), columns):
        row_items = items[i:i + columns]
        row_parts = []
        for j, item in enumerate(row_items):
            truncated = truncate(item, col_width)
            if j < len(row_items) - 1:
                row_parts.append(align_text(truncated, col_width + gap, "left"))
            else:
                row_parts.append(truncated)
        result.append("".join(row_parts))

    return result
