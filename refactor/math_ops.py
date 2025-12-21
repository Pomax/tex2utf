"""
Mathematical operations for tex2utf.

This module implements the rendering of mathematical constructs:
- Fractions (stacked with horizontal bar)
- Subscripts and superscripts (positioned above/below baseline)
- Square roots (with radical sign)
- Overlines and underlines
- Accents (hat, tilde, etc.)
- Binomial coefficients
- Arrows with labels

Each function typically:
1. Retrieves the collected argument(s) from the output buffer
2. Transforms them into the appropriate 2D layout
3. Replaces the arguments with the combined result

Example - Fraction:
-------------------
Input: \\frac{a+b}{c}
Collected: ["a+b", "c"]
Output:
    a+b
    ───
     c

Function Naming Convention:
---------------------------
- f_*: Functions called as callbacks when groups complete
- Most take no arguments (data comes from state.out)
- Some take string arguments passed via callsub mechanism
"""

import re
import unicodedata

from .config import debug_log
from .records import (
    empty, string2record, get_length, get_height, setbaseline,
    vStack, center, record_forcelength, vputs
)
from . import state


def f_subscript():
    """
    Handle subscript after collecting the subscript content.
    
    Sets up to also check for a following superscript (for combined sub/super).
    Called after _ and its argument have been parsed.
    """
    from . import stack
    
    # Change wait to expect 2 items (subscript + optional superscript)
    state.wait[-1] = 2
    state.action[-1] = "f_subSuper"
    
    # Check if superscript follows immediately
    if not re.match(r"\s*\^", state.par) and not re.match(r"\s*\\begin\s*\{Sp\}", state.par):
        stack.commit(empty())  # No superscript, commit empty placeholder
    else:
        # Remove the ^ and let it be processed as second item
        state.par = re.sub(r"^\s*\^", "", state.par)
        state.par = re.sub(r"^\s*\\begin\s*\{Sp\}", r"\\begin{matrix}", state.par)


def f_superscript():
    """
    Handle superscript after collecting the superscript content.
    
    Sets up to also check for a following subscript (for combined super/sub).
    Called after ^ and its argument have been parsed.
    """
    from . import stack
    
    state.wait[-1] = 2
    state.action[-1] = "f_superSub"
    
    if not re.match(r"\s*_", state.par) and not re.match(r"\s*\\begin\s*\{Sb\}", state.par):
        stack.commit(empty())
    else:
        state.par = re.sub(r"^\s*_", "", state.par)
        state.par = re.sub(r"^\s*\\begin\s*\{Sb\}", r"\\begin{matrix}", state.par)


def f_subSuper():
    """Process subscript followed by optional superscript."""
    from . import stack
    
    stack.trim(2)
    stack.collapse(2)
    if not stack.assertHave(2):
        stack.finish("", True)
        return
    sup_sub(0, 1)  # Subscript at offset 1, superscript at offset 0


def f_superSub():
    """Process superscript followed by optional subscript."""
    from . import stack
    
    stack.trim(2)
    stack.collapse(2)
    if not stack.assertHave(2):
        stack.finish("", True)
        return
    sup_sub(1, 0)  # Superscript at offset 1, subscript at offset 0


def sup_sub(p1_off: int, p2_off: int):
    """
    Combine superscript and subscript into a single stacked record.
    
    Creates output like:
         n      (superscript)
        x       (baseline - empty row)
         m      (subscript)
    
    Args:
        p1_off: Offset from end of out[] for superscript (0 or 1)
        p2_off: Offset from end of out[] for subscript (0 or 1)
    """
    from . import stack
    
    # Get the two items from output buffer
    p1 = len(state.out) - 1 - p1_off  # Superscript position
    p2 = len(state.out) - 1 - p2_off  # Subscript position
    parts1 = state.out[p1].split(",", 4)
    parts2 = state.out[p2].split(",", 4)
    h1, l1 = int(parts1[0]) or 1, int(parts1[1])
    h2, l2 = int(parts2[0]) or 1, int(parts2[1])
    str1 = parts1[4] if len(parts1) > 4 else ""
    str2 = parts2[4] if len(parts2) > 4 else ""
    
    # Handle case where both are empty
    if l1 == 0 and l2 == 0:
        stack.finish(2, True)
        return
    
    l = max(l1, l2)
    state.chunks.pop()
    state.out.pop()
    
    # Build stacked result based on what's present
    if l1 == 0:  # No superscript, only subscript
        h = h2 + 1
        state.out[-1] = f"{h},{l},0,0,\n{str2}"
    elif l2 == 0:  # No subscript, only superscript
        h = h1 + 1
        state.out[-1] = f"{h},{l},{h1},0,{str1}\n"
    else:  # Both present
        h = h1 + h2 + 1
        state.out[-1] = f"{h},{l},{h1},0,{str1}\n\n{str2}"

    # Add trailing space for visual separation when subscript exists
    # This helps with spacing after things like \sum_{i=1}^{n}
    parts = state.out[-1].split(",", 4)
    result_h = int(parts[0]) or 1
    if result_h > 1 and l2 != 0 and len(state.level) <= 3:
        result_l = int(parts[1])
        result_b = int(parts[2])
        content = parts[4] if len(parts) > 4 else ""
        lines = content.split("\n") if content else [""] * result_h
        while len(lines) < result_h:
            lines.append("")
        lines = [line.ljust(result_l) + " " for line in lines]
        state.out[-1] = f"{result_h},{result_l+1},{result_b},0," + "\n".join(lines)

    stack.finish(2, True)


def f_fraction():
    """
    Build a fraction from numerator and denominator.
    
    Creates:
        numerator
        ─────────
        denominator
    
    The fraction bar uses Unicode box-drawing character ─.
    Numerator and denominator are centered.
    """
    from . import stack
    from .join import join_records
    
    debug_log(f"f_fraction called")
    stack.trim(2)
    stack.collapse(2)
    if not stack.assertHave(2):
        debug_log("f_fraction: not enough chunks")
        stack.finish("", True)
        return
    
    # Get numerator and denominator
    numer = state.out[-2]
    denom = state.out[-1]
    debug_log(f"f_fraction: numer={numer}, denom={denom}")
    
    # Calculate width (max of numerator and denominator)
    l1, l2 = get_length(numer), get_length(denom)
    length = max(l1, l2)
    
    # Center both parts and add fraction bar
    numer_centered = center(length, numer)
    denom_centered = center(length, denom)
    line_rec = string2record("─" * length)  # Fraction bar
    
    # Stack: numerator, then bar, then denominator
    result = vStack(vStack(numer_centered, line_rec), denom_centered)
    
    # Set baseline at the fraction bar
    numer_h = get_height(numer_centered)
    result = setbaseline(result, numer_h)
    debug_log(f"f_fraction: result={result}")

    # Add leading space if preceded by content (for visual separation)
    frac_group_start = state.chunks[state.level[-1]] if state.level else 0
    check_idx = frac_group_start - 1
    debug_log(
        f"f_fraction: frac_group_start={frac_group_start}, check_idx={check_idx}, len(out)={len(state.out)}"
    )

    if check_idx >= 0 and check_idx < len(state.out):
        prev_parts = state.out[check_idx].split(",", 4)
        prev_s = prev_parts[4] if len(prev_parts) > 4 else ""
        prev_l = int(prev_parts[1]) if len(prev_parts) > 1 and prev_parts[1] else 0
        debug_log(f"f_fraction: prev_s='{prev_s}', prev_l={prev_l}")
        if prev_l > 0 and prev_s:
            if not prev_s.endswith(" "):
                last_char = prev_s.rstrip()[-1:] if prev_s.rstrip() else ""
                if last_char and last_char not in "+-=(<[{":
                    debug_log(f"f_fraction: adding leading space")
                    result = join_records(string2record(" "), result)

    # Add trailing space if followed by certain content
    next_content = state.par.lstrip()
    debug_log(f"f_fraction: next_content starts with '{next_content[:20] if next_content else ''}'")
    if next_content:
        add_trailing_space = False
        
        if next_content[0] == "\\":
            match = re.match(r"^\\([a-zA-Z]+)", next_content)
            if match:
                cmd_name = match.group(1)
                # Commands that don't need space before them
                no_space_cmds = {
                    "right", "end", "bigr", "Bigr", "biggr", "Biggr",
                    "cdot", "cdots", "times", "div", "pm", "mp",
                    "cap", "cup", "wedge", "vee", "oplus", "otimes", "ominus"
                }
                if cmd_name not in no_space_cmds:
                    add_trailing_space = True
        elif next_content[0] not in "+-=)>]}^_,;:\\ ":
            if unicodedata.category(next_content[0]).startswith("L") or next_content[0] in "([<":
                add_trailing_space = True

        if add_trailing_space:
            debug_log(f"f_fraction: adding trailing space")
            result = join_records(result, string2record(" "))

    # Replace the two arguments with the fraction
    state.out[-2] = result
    state.chunks.pop()
    state.out.pop()
    stack.finish(2, True)


def f_choose():
    """
    Build a binomial coefficient (n choose k).
    
    Creates:
        ╭   ╮
        │ n │
        │   │
        │ k │
        ╰   ╯
    """
    from . import stack
    from .brackets import makehigh_inplace
    
    stack.trim(2)
    stack.collapse(2)
    if not stack.assertHave(2):
        stack.finish("", True)
        return
    
    # Stack n over k with space between
    l1, l2 = get_length(state.out[-2]), get_length(state.out[-1])
    length = max(l1, l2)
    state.out[-1] = vStack(
        vStack(center(length, state.out[-2]), string2record(" " * length)),
        center(length, state.out[-1]),
    )
    
    # Add parentheses
    state.chunks.append(len(state.out))
    state.out.append(empty())
    state.out[-3] = string2record("(")
    state.out[-1] = string2record(")")
    
    # Make parentheses tall enough
    parts = state.out[-2].split(",", 4)
    h, b = int(parts[0]), int(parts[2])
    makehigh_inplace(state.out, -3, h, b, 0, 1)
    makehigh_inplace(state.out, -1, h, b, 1, 0)
    stack.finish(2, True)


def f_radical():
    """
    Build a square root symbol around content.
    
    Creates:
         ┌───┐
         │ x │
        ⟍│   │
    
    Uses Unicode box-drawing characters for the radical.
    """
    from . import stack
    
    stack.trim(1)
    stack.collapse(1)
    if not stack.assertHave(1):
        stack.finish("", True)
        return
    
    parts = state.out[-1].split(",", 4)
    h, l, b = int(parts[0]) or 1, int(parts[1]), int(parts[2])
    content = parts[4] if len(parts) > 4 else ""
    lines = content.split("\n") if content else [""]
    while len(lines) < h:
        lines.append("")

    # Build radical: top bar, then content with left border
    result_lines = [" ┌" + "─" * l + "┐"]  # Top bar with corners

    for i in range(h):
        line_padded = lines[i].ljust(l)
        if i == h - 1:
            # Bottom line gets the radical symbol
            result_lines.append("⟍│" + line_padded + " ")
        else:
            result_lines.append(" │" + line_padded + " ")

    new_h = h + 1
    new_l = l + 3  # 2 for left side, 1 for right
    new_b = b + 1
    state.out[-1] = f"{new_h},{new_l},{new_b},0," + "\n".join(result_lines)
    stack.finish(1, True)


def f_overline():
    """
    Add an overline above content.
    
    Creates:
        ___
        abc
    """
    from . import stack
    
    stack.trim(1)
    stack.collapse(1)
    if not stack.assertHave(1):
        stack.finish("", True)
        return
    parts = state.out[-1].split(",", 4)
    h, l, b = int(parts[0]) or 1, int(parts[1]), int(parts[2])
    state.out[-1] = vStack(string2record("_" * l), state.out[-1])
    state.out[-1] = setbaseline(state.out[-1], b + 1)
    stack.finish(1, True)


def f_underline():
    """
    Add an underline below content.
    
    Creates:
        abc
        ‾‾‾
    """
    from . import stack
    
    stack.trim(1)
    stack.collapse(1)
    if not stack.assertHave(1):
        stack.finish("", True)
        return
    parts = state.out[-1].split(",", 4)
    h, l, b = int(parts[0]) or 1, int(parts[1]), int(parts[2])
    state.out[-1] = vStack(state.out[-1], string2record("‾" * l))
    state.out[-1] = setbaseline(state.out[-1], b)
    stack.finish(1, True)


def f_not():
    """
    Handle negation (\\not) - typically produces ≠, ∤, or ∉.
    """
    from . import stack
    from .join import join_records
    
    stack.collapse(1)
    if not stack.assertHave(1):
        stack.finish("", True)
        return
    parts = state.out[-1].split(",", 4)
    s = parts[4] if len(parts) > 4 else ""
    
    # Map common negations
    if s == "=":
        state.out[-1] = state.contents.get("\\neq", string2record("≠"))
    elif s.strip() == "|":
        state.out[-1] = state.contents.get("\\nmid", string2record("∤"))
    elif state.out[-1] == state.contents.get("\\in"):
        state.out[-1] = state.contents.get("\\notin", string2record("∉"))
    else:
        state.out[-1] = join_records(string2record("\\not"), state.out[-1])
    stack.finish(1, True)


def f_putover(rec_or_str, no_finish: bool = False):
    """
    Put an accent or symbol over the current content.
    
    Used for \\hat, \\tilde, \\dot, etc.
    
    Args:
        rec_or_str: The accent to place (record string or plain string)
        no_finish: If True, don't call finish (for compound operations)
    """
    from . import stack
    
    # Handle both record string and plain string
    if isinstance(rec_or_str, str) and not rec_or_str.startswith(("0,", "1,", "2,", "3,", "4,", "5,", "6,", "7,", "8,", "9,")):
        rec = string2record(rec_or_str)
    else:
        rec = rec_or_str
    
    stack.trim(1)
    stack.collapse(1)
    if not stack.assertHave(1):
        stack.finish("", True)
        return
    parts = state.out[-1].split(",", 4)
    h, l1, b = int(parts[0]) or 1, int(parts[1]), int(parts[2])
    l2 = get_length(rec)
    length = max(l1, l2)
    parts_rec = rec.split(",", 4)
    b1 = int(parts_rec[0]) or 1
    b += b1 + 1
    state.out[-1] = vStack(center(length, rec), center(length, state.out[-1]))
    state.out[-1] = setbaseline(state.out[-1], b)
    if not no_finish:
        stack.finish(1, True)


def f_putunder(rec: str):
    """
    Put a symbol under the current content.
    
    Args:
        rec: The symbol to place below (as a record string)
    """
    from . import stack
    
    stack.trim(1)
    stack.collapse(1)
    if not stack.assertHave(1):
        stack.finish("", True)
        return
    parts = state.out[-1].split(",", 4)
    h, l1, b = int(parts[0]) or 1, int(parts[1]), int(parts[2])
    l2 = get_length(rec)
    length = max(l1, l2)
    state.out[-1] = vStack(center(length, state.out[-1]), center(length, rec))
    state.out[-1] = setbaseline(state.out[-1], b)
    stack.finish(1, True)


def f_putover_string(s: str):
    """
    Put a string as an accent over content.
    
    Convenience wrapper for f_putover.
    
    Args:
        s: The accent character(s)
    """
    f_putover(string2record(s))


def f_widehat():
    """
    Create a wide hat accent that spans the content width.
    
    Creates /~~~\\ for wide content, ^ for narrow.
    """
    from . import stack
    
    stack.trim(1)
    stack.collapse(1)
    l = get_length(state.out[-1])
    if l <= 1:
        f_putover(string2record("^"))
    else:
        f_putover(string2record("/" + "~" * (l - 2) + "\\"))


def f_widetilde():
    """
    Create a wide tilde accent that spans the content width.
    """
    from . import stack
    
    stack.trim(1)
    stack.collapse(1)
    l = get_length(state.out[-1])
    if l <= 1:
        f_putover(string2record("~"))
    elif l <= 3:
        f_putover(string2record("/\\/"))
    else:
        l1 = l // 2 - 1
        f_putover(string2record("/" + "~" * l1 + "\\" + "_" * (l - 3 - l1) + "/"))


def f_putpar(delims: str):
    """
    Wrap content in delimiters (parentheses, brackets, etc.).
    
    Args:
        delims: "left;right" delimiter pair, e.g., "(;)" or "[;]"
    """
    from . import stack
    from .join import join_records
    
    stack.trim(1)
    l, r = delims.split(";")
    stack.collapse(1)
    if not stack.assertHave(1):
        stack.finish("", True)
        return
    state.out[-1] = join_records(string2record(l), join_records(state.out[-1], string2record(r)))
    stack.finish(1, True)


def f_buildrel():
    """
    Handle \\buildrel command (put one thing over another with relation).
    
    Syntax: \\buildrel expr1 \\over expr2
    """
    from . import stack
    
    stack.trim(3)
    stack.collapse(3)
    if not stack.assertHave(3):
        stack.finish("", True)
        return
    rec = state.out[-3]
    state.out[-3] = state.out[-1]
    state.chunks[:] = state.chunks[:-2]
    state.out[:] = state.out[:-2]
    f_putover(rec, True)
    stack.finish(3, True)


def f_literal_no_length():
    """
    Mark content as having zero logical width.
    
    Used for content that shouldn't affect layout calculations.
    """
    from . import stack
    
    stack.collapse(1)
    if not stack.assertHave(1):
        stack.finish("", True)
        return
    state.out[-1] = record_forcelength(state.out[-1], 0)
    stack.finish(1, True)


def f_arrow(tips: str):
    """
    Create a horizontal arrow with labels above and below.
    
    Used for commutative diagrams: @>label>> or @<label<<
    
    Args:
        tips: "left_tip;right_tip", e.g., "<;>" or ";>"
    """
    from . import stack
    
    l, r = tips.split(";")
    stack.trim(2)
    stack.collapse(2)
    if not stack.assertHave(2):
        stack.finish("", True)
        return
    l1, l2 = get_length(state.out[-2]), get_length(state.out[-1])
    length = max(l1, l2)
    
    # Stack: label above, arrow, label below
    state.out[-2] = vStack(
        vStack(
            center(length + 4, state.out[-2]),
            string2record(f" {l}" + "-" * (length + 1) + f"{r} "),
        ),
        center(length + 4, state.out[-1]),
    )
    state.chunks.pop()
    state.out.pop()
    stack.finish(2, True)


def f_arrow_v(tips: str):
    """
    Create a vertical arrow with labels on sides.
    
    Used for commutative diagrams: @VlabelVV or @AlabelAA
    
    Args:
        tips: "top_tip;bottom_tip"
    """
    from . import stack
    from .join import join_records
    
    l, r = tips.split(";")
    stack.trim(2)
    stack.collapse(2)
    if not stack.assertHave(2):
        stack.finish("", True)
        return
    parts1 = state.out[-2].split(",", 4)
    parts2 = state.out[-1].split(",", 4)
    h1, b1 = int(parts1[0]) or 1, int(parts1[2])
    h2, b2 = int(parts2[0]) or 1, int(parts2[2])
    b = max(b1, b2)
    res = join_records(state.out[-2], state.out[-1])
    parts = res.split(",", 4)
    h = int(parts[0]) or 1
    bb = b + 1
    state.out[-2] = vStack(vputs(" " * (b - b1 + 1)), state.out[-2])
    state.out[-2] = setbaseline(state.out[-2], bb)
    state.out[-1] = vStack(vputs(" " * (b - b2 + 1)), state.out[-1])
    state.out[-1] = setbaseline(state.out[-1], bb)
    state.out[-2] = join_records(
        join_records(state.out[-2], vputs(l + "|" * (h + 1) + r, b + 1)), state.out[-1]
    )
    state.chunks.pop()
    state.out.pop()
    stack.finish(2, True)
