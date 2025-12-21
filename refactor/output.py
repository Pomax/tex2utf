"""
Output and printing functions for tex2utf.

This module handles the final stages of output processing:
- Printing records to stdout
- Line breaking for long lines
- Text justification (expanding spaces to fill line width)

The output process involves:
1. Collecting records in the output buffer
2. When ready to print, joining all records horizontally
3. Optionally justifying text by expanding spaces
4. Printing each line, stripping common indentation
"""

import re
from .config import debug_log
from .records import empty, string2record, get_length, cut
from . import state


def printrecord(rec: str):
    """
    Print a record to stdout.

    Handles multi-line records by:
    - Splitting into individual lines
    - Removing trailing whitespace from each line
    - Removing common leading whitespace (de-indenting)
    - Printing non-empty lines

    Args:
        rec: A record string to print
    """
    parts = rec.split(",", 4)
    s = parts[4] if len(parts) > 4 else ""
    debug_log(f"printrecord: rec={rec[:100]}...")
    debug_log(f"  parts[0-3]={parts[0]},{parts[1]},{parts[2]},{parts[3]}")
    debug_log(f"  s has {s.count(chr(10))} newlines")
    lines = s.split("\n")
    for i, line in enumerate(lines[:6]):
        debug_log(f"  line {i} (len={len(line)}): '{line}'")

    # Remove trailing whitespace and empty lines
    lines = [line.rstrip() for line in lines if line.rstrip() != ""]

    if not lines:
        return

    # Find minimum indentation across all lines
    min_indent = None
    for line in lines:
        if line:
            leading = len(line) - len(line.lstrip())
            if min_indent is None or leading < min_indent:
                min_indent = leading

    # Remove common indentation
    if min_indent and min_indent > 0:
        lines = [
            line[min_indent:] if len(line) >= min_indent else line for line in lines
        ]

    print("\n".join(lines))


def exp_sp_maker(fr: int, re_val: int):
    """
    Create a space expander function for text justification.

    Returns a function that replaces each space with multiple spaces
    to justify text to fill the line width.

    Args:
        fr: Base number of extra spaces per space
        re_val: Number of spaces that get one additional space

    Returns:
        A function suitable for use with re.sub
    """
    c1, c2 = [0], [0]

    def exp_sp(match):
        c1[0] += 1
        if c1[0] > re_val:
            c2[0] = 0
        return " " * (c2[0] + fr + 1)

    return exp_sp


def do_print(force: bool = False):
    """
    Print the current output buffer.

    This is the main output function. It:
    1. Determines how much of the buffer to print
    2. Optionally justifies the text (if not ragged mode)
    3. Joins all records horizontally
    4. Prints the result
    5. Clears the printed portion from the buffer

    Args:
        force: If True, print even if buffer isn't full
    """
    from . import config
    from .join import join_records

    # Determine last record to print
    last = state.chunks[state.level[1]] - 1 if len(state.level) > 1 else len(state.out) - 1
    if last < 0:
        return

    # Calculate total length
    l = sum(get_length(state.out[i]) for i in range(last + 1))
    state.curlength = l

    # Justify text if needed (expand spaces to fill line width)
    if not force and l <= config.linelength:
        extra = config.linelength - state.curlength
        if extra > 0 and not config.opt_ragged:
            # Count expandable spaces
            exp = 0
            for i in range(last + 1):
                parts = state.out[i].split(",", 4)
                h = int(parts[0])
                s = parts[4] if len(parts) > 4 else ""
                if not h:  # Only single-line records have expandable spaces
                    exp += s.count(" ")
            if exp:
                # Distribute extra space among spaces
                re_val = extra % exp
                fr = (extra - re_val) // exp
                expander = exp_sp_maker(fr, re_val)
                for i in range(last + 1):
                    parts = state.out[i].split(",", 4)
                    h = int(parts[0])
                    s = parts[4] if len(parts) > 4 else ""
                    if not h:
                        s = re.sub(r" ", expander, s)
                        state.out[i] = string2record(s)

    # Join all records and print
    if last >= 0:
        result = state.out[0]
        for i in range(1, last + 1):
            result = join_records(result, state.out[i])
        printrecord(result)

    # Clear printed portion from buffer
    state.curlength = 0
    if len(state.out) > last + 1:
        state.out = state.out[last + 1 :]
        for i in range(len(state.chunks)):
            state.chunks[i] -= last + 1
    else:
        state.out = []
    if len(state.level) > 1:
        state.chunks = state.chunks[:1] + state.chunks[state.level[1] :]
    else:
        state.chunks = [0]


def prepare_cut(rec: str) -> str:
    """
    Prepare a record for line breaking if it's too long.

    Attempts to break at spaces to keep lines within linelength.
    Used when a record would exceed the maximum line width.

    Args:
        rec: A record that may be too long

    Returns:
        The (possibly truncated) record, with earlier portions already printed
    """
    from . import config

    if len(state.level) != 1:
        return rec

    lenadd = get_length(rec)
    lenrem = config.linelength - state.curlength

    if lenadd + state.curlength <= config.linelength:
        return rec

    parts = rec.split(",", 4)
    h = int(parts[0])
    s = parts[4] if len(parts) > 4 else ""

    # Only break single-line records at spaces
    if h < 2:
        while lenrem < lenadd:
            idx = s.rfind(" ", 0, lenrem)
            if idx > -1:
                p = cut(idx + 1, rec)
                state.out.append(p[0])
                state.curlength += idx + 1
                do_print()
                rec = p[1]
                parts = rec.split(",", 4)
                lenadd = int(parts[1])
                s = parts[4] if len(parts) > 4 else ""
                lenrem = config.linelength
            else:
                break

    # Force break if still too long
    if lenadd > config.linelength and lenrem:
        p = cut(lenrem, rec)
        state.out.append(p[0])
        state.curlength += lenrem
        do_print()
        rec = p[1]

    do_print()

    # Break remaining content if still too long
    while get_length(rec) > config.linelength:
        p = cut(config.linelength, rec)
        state.out[:] = [p[0]]
        do_print()
        rec = p[1]

    state.curlength = 0
    return rec
