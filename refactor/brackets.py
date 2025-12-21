"""
Bracket handling and generation functions for tex2utf.

This module handles the creation of "tall" delimiters - parentheses,
brackets, braces, and angle brackets that stretch to match the height
of their contents. This is essential for proper mathematical notation
where delimiters must visually encompass their contents.

For example, a 3-line tall fraction needs 3-line tall parentheses:

    ╭     ╮
    │ a+b │
    │ ─── │
    │  c  │
    ╰     ╯

Unicode Box Drawing Characters Used:
------------------------------------
- Parentheses: ╭ ╮ ╰ ╯ │
- Brackets: ┌ ┐ └ ┘ │
- Braces: ╭ ╮ ╰ ╯ │ ╡ ╞
- Angle brackets: ⟨ ⟩ ⧸ ⧹

Functions:
----------
- regenerate_angle_bracket(): Create angle bracket at specific height
- makecompound(): Build tall delimiter from component characters
- makehigh_inplace(): Expand a delimiter in the output buffer
"""

from .config import debug_log
from .records import string2record, vputs


def regenerate_angle_bracket(bracket_type: str, h: int, b: int) -> tuple:
    """
    Generate angle bracket lines with correct alignment.

    Creates a tall angle bracket (⟨ or ⟩) that spans the given height,
    with the tip at the baseline and slanted lines above and below.

    Args:
        bracket_type: "<" for left angle, ">" for right angle
        h: Desired height in lines
        b: Baseline position (where the tip goes)

    Returns:
        Tuple of (lines, width) where lines is a list of strings
    """
    max_dist = max(b, h - b - 1)
    width = max_dist + 1

    result_lines = []
    for row in range(h):
        dist_from_baseline = abs(row - b)

        if bracket_type == "<":
            # Left angle: tip on left, slants go right
            col = dist_from_baseline
            if row < b:
                char = "⧸"  # Upper arm
            elif row == b:
                char = "⟨"  # Tip
            else:
                char = "⧹"  # Lower arm
        else:  # '>'
            # Right angle: tip on right, slants go left
            col = width - 1 - dist_from_baseline
            if row < b:
                char = "⧹"  # Upper arm
            elif row == b:
                char = "⟩"  # Tip
            else:
                char = "⧸"  # Lower arm

        line = " " * col + char
        result_lines.append(line)

    max_w = max(len(line) for line in result_lines) if result_lines else 1
    return [line.ljust(max_w) for line in result_lines], max_w


def makecompound(
    ascent: int,
    descent: int,
    base: str,
    exp_one: str,
    exp_real: str,
    top: str,
    bottom: str,
    middle: str,
) -> str:
    """
    Create a compound bracket character from component pieces.

    Builds a tall delimiter by combining top, middle, bottom, and
    extension characters. Used for parentheses, brackets, and braces.

    Args:
        ascent: Number of lines above baseline (including baseline)
        descent: Number of lines below baseline
        base: Single-line version of the character
        exp_one: Extension character for height 2
        exp_real: Extension character for taller heights
        top: Top cap character
        bottom: Bottom cap character
        middle: Middle character (for braces)

    Returns:
        String with one character per line (to be used with vputs)
    """
    if ascent >= 1 and descent > 0 and exp_real == middle:
        return top + exp_real * (ascent + descent - 2) + bottom
    if descent <= 0:
        return exp_one * (ascent - 1) + base
    if ascent <= 1:
        return base + exp_one * descent
    above = top + exp_real * (ascent - 2) if ascent >= 2 else top
    below = exp_real * (descent - 1) + bottom if descent > 1 else bottom
    return above + middle + below


def makehigh_inplace(out: list, idx: int, h: int, b: int, left_sp: int, right_sp: int):
    """
    Expand a delimiter to a given height, modifying the output buffer in place.

    Takes a simple delimiter character (like "(" or "[") and replaces it
    with a tall version using Unicode box-drawing characters.

    Args:
        out: The output buffer (list of records)
        idx: Index into the buffer (can be negative)
        h: Desired height
        b: Baseline position
        left_sp: Spaces to add on the left
        right_sp: Spaces to add on the right
    """
    from .join import join_records

    parts = out[idx].split(",", 4)
    s = parts[4] if len(parts) > 4 else ""
    debug_log(
        f"makehigh_inplace: idx={idx}, h={h}, b={b}, left_sp={left_sp}, right_sp={right_sp}, s='{s}'"
    )

    # Handle empty delimiter (\\left. or \\right.)
    if s == ".":
        out[idx] = f"{parts[0]},{parts[1]},{parts[2]},{parts[3]}, "
        return

    h = h if h > 0 else 1
    d = h - b - 1  # Descent (lines below baseline)

    # Don't expand if already small enough
    if h < 2 or (h == 2 and s in "()<>"):
        return

    # Character specifications: [base, exp_one, exp_real, top, bottom, middle]
    c = None
    if s == "(":
        c = ["(", " ", "│", "╭", "╰", "│"]
    elif s == ")":
        c = [")", " ", "│", "╮", "╯", "│"]
    elif s == "{":
        c = ["{", " ", "│", "╭", "╰", "╡"]
    elif s == "}":
        c = ["}", " ", "│", "╮", "╯", "╞"]
    elif s in ("|", "||"):
        # Vertical bars (for determinants, norms, etc.)
        if h >= 3:
            if left_sp == 0:  # Left delimiter
                c = ["|", " ", "│", "╭", "╰", "│"]
            else:  # Right delimiter
                c = ["|", " ", "│", "╮", "╯", "│"]
        else:
            c = ["|", "|", "|", "|", "|", "|"]
    elif s == "[":
        c = ["[", " ", "│", "┌", "└", "│"]
    elif s == "]":
        c = ["]", " ", "│", "┐", "┘", "│"]
    elif s in ("<", ">"):
        # Angle brackets need special handling
        if h == 2:
            return

        max_dist = max(b, h - b - 1)
        width = max_dist + 1

        result_lines = []
        for row in range(h):
            dist_from_baseline = abs(row - b)

            if s == "<":
                col = dist_from_baseline
                if row < b:
                    char = "⧸"
                elif row == b:
                    char = "⟨"
                else:
                    char = "⧹"
            else:
                col = width - 1 - dist_from_baseline
                if row < b:
                    char = "⧹"
                elif row == b:
                    char = "⟩"
                else:
                    char = "⧸"

            line = " " * col + char
            result_lines.append(line)

        max_w = max(len(line) for line in result_lines) if result_lines else 1
        result_lines = [line.ljust(max_w) for line in result_lines]
        rec = f"{h},{max_w},{b},0," + "\n".join(result_lines)
        debug_log(f"makehigh_inplace angle bracket '{s}': h={h}, max_w={max_w}, b={b}")
        debug_log(f"  result_lines={result_lines}")

        if left_sp:
            rec = join_records(string2record(" " * left_sp), rec)
        if right_sp:
            rec = join_records(rec, string2record(" " * right_sp))
        out[idx] = rec
        return
    else:
        return

    # Build the tall delimiter using makecompound
    compound = makecompound(b + 1, d, *c)
    out[idx] = vputs(compound, b)

    # Handle double bars (||)
    if len(s) == 2:
        out[idx] = join_records(out[idx], out[idx])

    # Add spacing
    if left_sp:
        out[idx] = join_records(string2record(" " * left_sp), out[idx])
    if right_sp:
        out[idx] = join_records(out[idx], string2record(" " * right_sp))
