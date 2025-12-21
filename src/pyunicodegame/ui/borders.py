"""
pyunicodegame.ui.borders - Box-drawing character configurations.

QUICK START:
    from pyunicodegame.ui import BorderStyle

    single = BorderStyle.single()   # Single-line box:
    double = BorderStyle.double()   # Double-line box:
    heavy = BorderStyle.heavy()     # Heavy-weight box:
    rounded = BorderStyle.rounded() # Rounded corners:

    renderer.draw_box(0, 0, 20, 10, border_style=single)

CLASSES:
    BorderStyle: Configuration for box-drawing characters

Unicode box-drawing characters are used to create clean, aligned borders
that connect properly at corners and intersections.
"""

from dataclasses import dataclass


@dataclass
class BorderStyle:
    """
    Configuration for box-drawing border characters.

    Attributes:
        top_left: Top-left corner character
        top_right: Top-right corner character
        bottom_left: Bottom-left corner character
        bottom_right: Bottom-right corner character
        horizontal: Horizontal line character
        vertical: Vertical line character
        cross: Cross/intersection character (for grids)
        t_down: T-junction pointing down
        t_up: T-junction pointing up
        t_right: T-junction pointing right
        t_left: T-junction pointing left
    """
    top_left: str = "+"
    top_right: str = "+"
    bottom_left: str = "+"
    bottom_right: str = "+"
    horizontal: str = "-"
    vertical: str = "|"
    cross: str = "+"
    t_down: str = "+"
    t_up: str = "+"
    t_right: str = "+"
    t_left: str = "+"

    @classmethod
    def ascii(cls) -> "BorderStyle":
        """
        Plain ASCII box-drawing characters.

        Uses +, -, and | characters for maximum compatibility.

        Example:
            +--------+
            |        |
            +--------+
        """
        return cls(
            top_left="+",
            top_right="+",
            bottom_left="+",
            bottom_right="+",
            horizontal="-",
            vertical="|",
            cross="+",
            t_down="+",
            t_up="+",
            t_right="+",
            t_left="+",
        )

    @classmethod
    def single(cls) -> "BorderStyle":
        """
        Unicode single-line box-drawing characters.

        Uses U+250x range characters for clean single lines.

        Example:



        """
        return cls(
            top_left="\u250c",      #
            top_right="\u2510",     #
            bottom_left="\u2514",   #
            bottom_right="\u2518",  #
            horizontal="\u2500",    #
            vertical="\u2502",      #
            cross="\u253c",         #
            t_down="\u252c",        #
            t_up="\u2534",          #
            t_right="\u251c",       #
            t_left="\u2524",        #
        )

    @classmethod
    def double(cls) -> "BorderStyle":
        """
        Unicode double-line box-drawing characters.

        Uses U+255x range characters for double lines.

        Example:



        """
        return cls(
            top_left="\u2554",      #
            top_right="\u2557",     #
            bottom_left="\u255a",   #
            bottom_right="\u255d",  #
            horizontal="\u2550",    #
            vertical="\u2551",      #
            cross="\u256c",         #
            t_down="\u2566",        #
            t_up="\u2569",          #
            t_right="\u2560",       #
            t_left="\u2563",        #
        )

    @classmethod
    def heavy(cls) -> "BorderStyle":
        """
        Unicode heavy-weight box-drawing characters.

        Uses U+250x range heavy characters for bold lines.

        Example:



        """
        return cls(
            top_left="\u250f",      #
            top_right="\u2513",     #
            bottom_left="\u2517",   #
            bottom_right="\u251b",  #
            horizontal="\u2501",    #
            vertical="\u2503",      #
            cross="\u254b",         #
            t_down="\u2533",        #
            t_up="\u253b",          #
            t_right="\u2523",       #
            t_left="\u252b",        #
        )

    @classmethod
    def rounded(cls) -> "BorderStyle":
        """
        Unicode box-drawing with rounded corners.

        Uses single lines with arc corners for a softer look.

        Example:



        """
        return cls(
            top_left="\u256d",      #
            top_right="\u256e",     #
            bottom_left="\u2570",   #
            bottom_right="\u256f",  #
            horizontal="\u2500",    #
            vertical="\u2502",      #
            cross="\u253c",         #
            t_down="\u252c",        #
            t_up="\u2534",          #
            t_right="\u251c",       #
            t_left="\u2524",        #
        )

    @classmethod
    def dashed(cls) -> "BorderStyle":
        """
        Unicode dashed box-drawing characters.

        Uses dashed lines for a lighter appearance.
        """
        return cls(
            top_left="\u250c",      #
            top_right="\u2510",     #
            bottom_left="\u2514",   #
            bottom_right="\u2518",  #
            horizontal="\u2504",    #
            vertical="\u2506",      #
            cross="\u253c",         #
            t_down="\u252c",        #
            t_up="\u2534",          #
            t_right="\u251c",       #
            t_left="\u2524",        #
        )

    @classmethod
    def block(cls) -> "BorderStyle":
        """
        Block character borders using full and half blocks.

        Creates a more solid, filled appearance.
        """
        return cls(
            top_left="\u2588",      # Full block
            top_right="\u2588",
            bottom_left="\u2588",
            bottom_right="\u2588",
            horizontal="\u2580",    # Upper half block
            vertical="\u2588",      # Full block
            cross="\u2588",
            t_down="\u2588",
            t_up="\u2588",
            t_right="\u2588",
            t_left="\u2588",
        )
