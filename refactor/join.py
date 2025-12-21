"""
Record joining functions for tex2utf.

This module provides the join_records() function which horizontally
concatenates two records while properly handling baseline alignment.

This is separated from records.py to avoid circular imports, since
join_records needs to use bracket regeneration from brackets.py,
and brackets.py needs basic record functions.

The join operation is fundamental to building up complex mathematical
expressions - for example, joining "x" with "+" with "y" to get "x + y",
or joining a fraction with surrounding text.

Baseline Alignment:
-------------------
When joining records of different heights, they are aligned by their
baselines. For example, joining a tall fraction (baseline at the
fraction bar) with a simple letter (baseline at bottom) will position
the letter at the same vertical level as the fraction bar.
"""

from .config import debug_log
from .records import empty, string2record
from .brackets import regenerate_angle_bracket


def join_records(rec1: str, rec2: str) -> str:
    """
    Horizontally join two records with baseline alignment.

    The records are positioned so their baselines align. If one record
    is taller than the other, the shorter one is padded with blank lines
    above and/or below as needed.

    Special handling is included for angle brackets (⟨ ⟩) which need
    to be regenerated when adjacent content is taller than the original
    bracket.

    Args:
        rec1: Left record
        rec2: Right record

    Returns:
        Combined record with rec1 to the left of rec2
    """
    # Parse both records
    parts1 = rec1.split(",", 4)
    parts2 = rec2.split(",", 4)
    h1, l1, b1, sp1 = int(parts1[0]), int(parts1[1]), int(parts1[2]), int(parts1[3])
    h2, l2, b2, sp2 = int(parts2[0]), int(parts2[1]), int(parts2[2]), int(parts2[3])
    str1 = parts1[4] if len(parts1) > 4 else ""
    str2 = parts2[4] if len(parts2) > 4 else ""

    # Ensure minimum height of 1
    if not h1:
        h1 = 1
    if not h2:
        h2 = 1

    # Calculate combined dimensions with baseline alignment
    b = max(b1, b2)  # New baseline is the maximum
    below1 = h1 - b1 - 1  # Lines below baseline in rec1
    below2 = h2 - b2 - 1  # Lines below baseline in rec2
    h = b + max(below1, below2) + 1  # Total height
    l = l1 + l2  # Total width

    # Split content into lines
    lines1 = str1.split("\n") if str1 else []
    lines2 = str2.split("\n") if str2 else []
    while len(lines1) < h1:
        lines1.append("")
    while len(lines2) < h2:
        lines2.append("")

    # Check if lines1 is an angle bracket that needs extending
    # Angle brackets grow dynamically to match adjacent content height
    if h > h1 and l1 <= 6:
        content = "\n".join(lines1)
        is_left_angle = "⟨" in content and ("⧸" in content or "⧹" in content or h1 <= 2)
        is_right_angle = "⟩" in content and (
            "⧸" in content or "⧹" in content or h1 <= 2
        )

        if is_left_angle or is_right_angle:
            bracket_type = "<" if is_left_angle else ">"
            original_l1 = l1

            baseline_line = lines1[b1] if b1 < len(lines1) else ""
            leading_spaces = len(baseline_line) - len(baseline_line.lstrip())

            # Regenerate bracket at new height
            new_lines, new_w = regenerate_angle_bracket(bracket_type, h, b)

            if original_l1 > new_w:
                if leading_spaces > 0:
                    pad = original_l1 - new_w
                    new_lines = [" " * pad + line for line in new_lines]
                new_w = original_l1

            lines1 = [line.ljust(new_w) for line in new_lines]
            l1 = new_w
            h1 = h
            b1 = b
            l = l1 + l2
            debug_log(
                f"join_records: Extended {bracket_type} bracket to h={h}, width={l1}"
            )

    # Similarly check lines2 for angle brackets
    if h > h2 and l2 <= 6:
        content = "\n".join(lines2)
        is_left_angle = "⟨" in content and ("⧸" in content or "⧹" in content or h2 <= 2)
        is_right_angle = "⟩" in content and (
            "⧸" in content or "⧹" in content or h2 <= 2
        )

        if is_left_angle or is_right_angle:
            bracket_type = "<" if is_left_angle else ">"
            original_l2 = l2

            baseline_line = lines2[b2] if b2 < len(lines2) else ""
            leading_spaces = len(baseline_line) - len(baseline_line.lstrip())

            new_lines, new_w = regenerate_angle_bracket(bracket_type, h, b)

            if original_l2 > new_w:
                if leading_spaces > 0:
                    pad = original_l2 - new_w
                    new_lines = [" " * pad + line for line in new_lines]
                new_w = original_l2

            lines2 = [line.ljust(new_w) for line in new_lines]
            l2 = new_w
            h2 = h
            b2 = b
            l = l1 + l2
            debug_log(
                f"join_records: Extended {bracket_type} bracket to h={h}, width={l2}"
            )

    # Ensure baseline row of lines2 has content (for proper alignment)
    if b2 < len(lines2) and len(lines2[b2]) == 0:
        lines2[b2] = " " * l2

    # Build combined result with proper vertical alignment
    result = [""] * h

    # Place lines1 content
    for i in range(h1):
        idx = b - b1 + i  # Offset by baseline difference
        if 0 <= idx < h:
            result[idx] = lines1[i].ljust(l1)

    # Pad any missing rows on left side
    for i in range(h):
        if len(result[i]) < l1:
            result[i] = result[i].ljust(l1)

    # Append lines2 content
    for i in range(h2):
        idx = b - b2 + i
        if 0 <= idx < h:
            result[idx] = result[idx][:l1].ljust(l1) + lines2[i]

    # Debug logging for angle brackets
    if "⧸" in str1 or "⧹" in str1 or "⟨" in str1 or "⟩" in str1:
        debug_log(
            f"join_records LEFT angle bracket: h1={h1}, b1={b1}, h2={h2}, b2={b2}"
        )
        debug_log(f"  Calculated: h={h}, b={b}")
        debug_log(f"  lines1={lines1}")
        debug_log(f"  result={result}")

    return f"{h},{l},{b},{sp1+sp2}," + "\n".join(result)


# Add join_records to records module for convenience
def _setup_records_join():
    """Add join_records to records module."""
    from . import records
    records.join_records = join_records

_setup_records_join()
