"""Record manipulation functions for tex2utf.

This module defines the core data structure used throughout tex2utf:
the "record". A record represents a 2D block of text that can be
positioned and combined with other records.

Record Format:
--------------
Records are encoded as comma-separated strings with the format:
    "height,length,baseline,spaces,content"

Where:
- height: Number of lines (0 or 1 for single-line text)
- length: Width in characters
- baseline: Line index where the "main" content sits (for vertical alignment)
- spaces: Count of expandable spaces (for justification)
- content: The actual text, with lines separated by \\n

Example:
--------
A simple fraction a/b might be represented as:
    "3,1,1,0,a\\n─\\nb"
    
This is 3 lines tall, 1 character wide, baseline at line 1 (the fraction bar),
0 expandable spaces, and content showing 'a' over '─' over 'b'.

Functions:
----------
- empty(): Create an empty record
- string2record(): Convert a string to a record
- get_length(), get_height(): Query record dimensions
- setbaseline(): Modify the baseline
- cut(): Split a record at a given width
- vStack(): Vertically stack two records
- center(): Center a record within a given width
- vputs(): Create a vertical string (one char per line)
"""

import re


def empty() -> str:
    """
    Create an empty record with zero dimensions.
    
    Returns:
        An empty record string "0,0,0,0,"
    """
    return "0,0,0,0,"


def string2record(s: str, no_expand: bool = False) -> str:
    """
    Convert a plain string to a record.
    
    Args:
        s: The string to convert
        no_expand: If True, mark spaces as non-expandable (height=1)
                   If False, count spaces for justification (height=0)
    
    Returns:
        A record string representing the input
    """
    if no_expand:
        h, sp = 1, 0
    else:
        sp = s.count(" ") if s else 0
        h = 0
    return f"{h},{len(s)},0,{sp},{s}"


def get_length(rec: str) -> int:
    """
    Get the width (length) of a record.
    
    Args:
        rec: A record string
        
    Returns:
        The width in characters
    """
    match = re.match(r"^\d+,(\d+)", rec)
    return int(match.group(1)) if match else 0


def get_height(rec: str) -> int:
    """
    Get the height of a record in lines.
    
    Args:
        rec: A record string
        
    Returns:
        The height (minimum 1)
    """
    match = re.match(r"^(\d+)", rec)
    h = int(match.group(1)) if match else 0
    return h if h > 0 else 1


def setbaseline(rec: str, new_b: int) -> str:
    """
    Set the baseline of a record.
    
    The baseline indicates which line should align with adjacent content.
    
    Args:
        rec: A record string
        new_b: The new baseline index
        
    Returns:
        The modified record string
    """
    return re.sub(r"^(\d+,\d+,)(\d+)", f"\\g<1>{new_b}", rec)


def record_forcelength(rec: str, new_len: int) -> str:
    """
    Force a record to report a specific length.
    
    Used for special cases where visual width differs from logical width.
    
    Args:
        rec: A record string
        new_len: The new length value
        
    Returns:
        The modified record string
    """
    return re.sub(r"^(\d+,)(\d+)", f"\\g<1>{new_len}", rec)


def cut(length: int, rec: str):
    """
    Split a record at a given width.
    
    Used for line-breaking long content.
    
    Args:
        length: Position at which to cut
        rec: A record string
        
    Returns:
        Tuple of (left_part, right_part) records
    """
    parts = rec.split(",", 4)
    h, l, b, sp = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])
    s = parts[4] if len(parts) > 4 else ""
    l2 = l - length
    if l2 < 0:
        return rec, empty()
    if h:
        lines = s.split("\n") if s else [""] * h
        while len(lines) < h:
            lines.append("")
        st1 = "\n".join(line[:length] for line in lines)
        st2 = "\n".join(line[length:] for line in lines)
    else:
        st1 = s[:length]
        st2 = s[length:]
    return f"{h},{length},{b},0,{st1}", f"{h},{l2},{b},0,{st2}"


def vStack(rec1: str, rec2: str) -> str:
    """
    Vertically stack two records (rec1 on top of rec2).
    
    The baseline is set to the bottom of rec1.
    
    Args:
        rec1: Top record
        rec2: Bottom record
        
    Returns:
        Combined record with rec1 above rec2
    """
    parts1 = rec1.split(",", 4)
    parts2 = rec2.split(",", 4)
    h1, l1, b1 = int(parts1[0]), int(parts1[1]), int(parts1[2])
    h2, l2 = int(parts2[0]), int(parts2[1])
    str1 = parts1[4] if len(parts1) > 4 else ""
    str2 = parts2[4] if len(parts2) > 4 else ""
    if not h1:
        h1 = 1
    if not h2:
        h2 = 1
    h = h1 + h2
    l = max(l1, l2)
    b = h1 - 1
    lines1 = str1.split("\n") if str1 else [""]
    lines2 = str2.split("\n") if str2 else [""]
    while len(lines1) < h1:
        lines1.append("")
    while len(lines2) < h2:
        lines2.append("")
    all_lines = lines1 + lines2
    content = "\n".join(all_lines)
    return f"{h},{l},{b},0,{content}"


def center(length: int, rec: str) -> str:
    """
    Center a record within a given width.
    
    Adds padding on both sides to center the content.
    
    Args:
        length: Target width
        rec: A record string
        
    Returns:
        Centered record of the specified width
    """
    parts = rec.split(",", 4)
    h1, l1, b1 = int(parts[0]), int(parts[1]), int(parts[2])
    str1 = parts[4] if len(parts) > 4 else ""
    if not h1:
        h1 = 1
    left = length - l1
    if left <= 0:
        return rec
    left_pad = left // 2
    lines = str1.split("\n") if str1 else [""]
    while len(lines) < h1:
        lines.append("")
    result = "\n".join((" " * left_pad + line).ljust(length) for line in lines)
    return f"{h1},{length},{b1},0,{result}"


def vputs(s: str, baseline: int = 0) -> str:
    """
    Create a vertical record from a string (one character per line).
    
    Used for building tall bracket characters.
    
    Args:
        s: String to arrange vertically
        baseline: Which line is the baseline
        
    Returns:
        A vertical record
    """
    h = len(s)
    if h == 0:
        return empty()
    content = "\n".join(list(s))
    return f"{h},1,{baseline},0,{content}"


# Note: join_records is defined in join.py to avoid circular imports
# It will be added to this module's namespace by join.py
join_records = None
