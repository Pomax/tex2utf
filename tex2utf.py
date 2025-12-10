#!/usr/bin/env python3
"""
UTF8-massaged version of https://ctan.org/pkg/tex2mail
Converted to Python 3 from Perl
"""

import sys
import re
import argparse
from typing import List, Optional, Dict, Any

# Configuration
linelength = 150
maxdef = 400
debug = 0
opt_by_par = False
opt_TeX = True
opt_ragged = False
opt_noindent = False
opt_debug = False


def debug_log(msg):
    if opt_debug:
        print(f"DEBUG: {msg}", file=sys.stderr)


# Token patterns
notusualtokenclass = r"[\\${}^_~&@]"
usualtokenclass = r"[^\\${}^_~&@]"
macro = r"\\([^a-zA-Z]|([a-zA-Z]+\s*))"
active = f"{macro}|\\$\\$|{notusualtokenclass}"
tokenpattern = f"{usualtokenclass}|{active}"
multitokenpattern = f"{usualtokenclass}+|{active}"

# Global state
level: List[int] = [0]
chunks: List[int] = [0]
tokenByToken: List[int] = [0]
out: List[str] = []
wait: List[Any] = [""]
action: List[str] = [""]
curlength = 0
secondtime = 0
argStack: List[str] = []
par = ""

# Symbol tables
type_table: Dict[str, str] = {}
contents: Dict[str, str] = {}
args: Dict[str, int] = {}
defs: Dict[str, str] = {}
environment: Dict[str, str] = {}
environment_none: Dict[str, bool] = {}


def cut(length: int, rec: str):
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


def printrecord(rec: str):
    parts = rec.split(",", 4)
    s = parts[4] if len(parts) > 4 else ""
    debug_log(f"printrecord: rec={rec[:100]}...")
    debug_log(f"  parts[0-3]={parts[0]},{parts[1]},{parts[2]},{parts[3]}")
    debug_log(f"  s has {s.count(chr(10))} newlines")
    lines = s.split("\n")
    for i, line in enumerate(lines[:6]):
        debug_log(f"  line {i} (len={len(line)}): '{line}'")
    print(s)


def extend_angle_bracket(
    lines: list, old_h: int, old_b: int, new_h: int, new_b: int, bracket_type: str
) -> list:
    """Extend an angle bracket record to a new height/baseline."""
    # Determine which character to use for extension
    if bracket_type == "<":
        above_char = "⧸"
        below_char = "⧹"
    else:  # '>'
        above_char = "⧹"
        below_char = "⧸"

    # Calculate how many rows to add above and below
    add_above = new_b - old_b
    add_below = (new_h - new_b - 1) - (old_h - old_b - 1)

    result = []

    # Add rows above (with increasing padding)
    for i in range(add_above):
        padding = new_b - i - 1
        result.append(" " * padding + above_char)

    # Add original rows (adjusting padding for each)
    for i, line in enumerate(lines):
        if i < old_b:
            # Above baseline - add extra padding
            new_padding = (new_b - (old_b - i)) - (old_b - i - 1)
            if new_padding > 0:
                result.append(" " * (add_above) + line.rstrip())
            else:
                result.append(line)
        else:
            result.append(line)

    # Add rows below (with increasing padding)
    for i in range(add_below):
        padding = (old_h - old_b - 1) + i + 1
        result.append(" " * padding + below_char)

    return result


def regenerate_angle_bracket(bracket_type: str, h: int, b: int) -> list:
    """Generate angle bracket lines with correct alignment."""
    max_dist = max(b, h - b - 1)
    width = max_dist + 1

    result_lines = []
    for row in range(h):
        dist_from_baseline = abs(row - b)

        if bracket_type == "<":
            col = dist_from_baseline
            if row < b:
                char = "⧸"
            elif row == b:
                char = "⟨"
            else:
                char = "⧹"
        else:  # '>'
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
    return [line.ljust(max_w) for line in result_lines], max_w


def join_records(rec1: str, rec2: str) -> str:
    parts1 = rec1.split(",", 4)
    parts2 = rec2.split(",", 4)
    h1, l1, b1, sp1 = int(parts1[0]), int(parts1[1]), int(parts1[2]), int(parts1[3])
    h2, l2, b2, sp2 = int(parts2[0]), int(parts2[1]), int(parts2[2]), int(parts2[3])
    str1 = parts1[4] if len(parts1) > 4 else ""
    str2 = parts2[4] if len(parts2) > 4 else ""
    if not h1:
        h1 = 1
    if not h2:
        h2 = 1
    b = max(b1, b2)
    below1 = h1 - b1 - 1
    below2 = h2 - b2 - 1
    h = b + max(below1, below2) + 1
    l = l1 + l2
    lines1 = str1.split("\n") if str1 else []
    lines2 = str2.split("\n") if str2 else []
    while len(lines1) < h1:
        lines1.append("")
    while len(lines2) < h2:
        lines2.append("")

    # Check if lines1 is an angle bracket that needs extending
    if h > h1 and l1 <= 6:
        content = "\n".join(lines1)
        is_left_angle = "⟨" in content and ("⧸" in content or "⧹" in content or h1 <= 2)
        is_right_angle = "⟩" in content and (
            "⧸" in content or "⧹" in content or h1 <= 2
        )

        if is_left_angle or is_right_angle:
            bracket_type = "<" if is_left_angle else ">"
            original_l1 = l1

            # Detect leading spaces
            baseline_line = lines1[b1] if b1 < len(lines1) else ""
            leading_spaces = len(baseline_line) - len(baseline_line.lstrip())

            # Regenerate with correct height
            new_lines, new_w = regenerate_angle_bracket(bracket_type, h, b)

            # Preserve original width if larger (due to spacing)
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

    # Similarly check lines2
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

    if b2 < len(lines2) and len(lines2[b2]) == 0:
        lines2[b2] = " " * l2
    result = [""] * h
    for i in range(h1):
        idx = b - b1 + i
        if 0 <= idx < h:
            result[idx] = lines1[i].ljust(l1)
    for i in range(h):
        if len(result[i]) < l1:
            result[i] = result[i].ljust(l1)
    for i in range(h2):
        idx = b - b2 + i
        if 0 <= idx < h:
            result[idx] = result[idx][:l1].ljust(l1) + lines2[i]

    if "⧸" in str1 or "⧹" in str1 or "⟨" in str1 or "⟩" in str1:
        debug_log(
            f"join_records LEFT angle bracket: h1={h1}, b1={b1}, h2={h2}, b2={b2}"
        )
        debug_log(f"  Calculated: h={h}, b={b}")
        debug_log(f"  lines1={lines1}")
        debug_log(f"  result={result}")
    return f"{h},{l},{b},{sp1+sp2}," + "\n".join(result)


def get_length(rec: str) -> int:
    match = re.match(r"^\d+,(\d+)", rec)
    return int(match.group(1)) if match else 0


def get_height(rec: str) -> int:
    match = re.match(r"^(\d+)", rec)
    h = int(match.group(1)) if match else 0
    return h if h > 0 else 1


def setbaseline(rec: str, new_b: int) -> str:
    return re.sub(r"^(\d+,\d+,)(\d+)", f"\\g<1>{new_b}", rec)


def empty() -> str:
    return "0,0,0,0,"


def string2record(s: str, no_expand: bool = False) -> str:
    if no_expand:
        h, sp = 1, 0
    else:
        sp = s.count(" ") if s else 0
        h = 0
    return f"{h},{len(s)},0,{sp},{s}"


def record_forcelength(rec: str, new_len: int) -> str:
    return re.sub(r"^(\d+,)(\d+)", f"\\g<1>{new_len}", rec)


def vStack(rec1: str, rec2: str) -> str:
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
    h = len(s)
    if h == 0:
        return empty()
    content = "\n".join(list(s))
    return f"{h},1,{baseline},0,{content}"


def exp_sp_maker(fr: int, re_val: int):
    c1, c2 = [0], [0]

    def exp_sp(match):
        c1[0] += 1
        if c1[0] > re_val:
            c2[0] = 0
        return " " * (c2[0] + fr + 1)

    return exp_sp


def do_print(force: bool = False):
    global curlength, out, chunks, level
    last = chunks[level[1]] - 1 if len(level) > 1 else len(out) - 1
    if last < 0:
        return
    l = sum(get_length(out[i]) for i in range(last + 1))
    curlength = l
    if not force and l <= linelength:
        extra = linelength - curlength
        if extra > 0 and not opt_ragged:
            exp = 0
            for i in range(last + 1):
                parts = out[i].split(",", 4)
                h = int(parts[0])
                s = parts[4] if len(parts) > 4 else ""
                if not h:
                    exp += s.count(" ")
            if exp:
                re_val = extra % exp
                fr = (extra - re_val) // exp
                expander = exp_sp_maker(fr, re_val)
                for i in range(last + 1):
                    parts = out[i].split(",", 4)
                    h = int(parts[0])
                    s = parts[4] if len(parts) > 4 else ""
                    if not h:
                        s = re.sub(r" ", expander, s)
                        out[i] = string2record(s)
    if last >= 0:
        result = out[0]
        for i in range(1, last + 1):
            result = join_records(result, out[i])
        printrecord(result)
    curlength = 0
    if len(out) > last + 1:
        out = out[last + 1 :]
        for i in range(len(chunks)):
            chunks[i] -= last + 1
    else:
        out = []
    if len(level) > 1:
        chunks = chunks[:1] + chunks[level[1] :]
    else:
        chunks = [0]


def prepare_cut(rec: str) -> str:
    global curlength, out, chunks
    if len(level) != 1:
        return rec
    lenadd = get_length(rec)
    lenrem = linelength - curlength
    if lenadd + curlength <= linelength:
        return rec
    parts = rec.split(",", 4)
    h = int(parts[0])
    s = parts[4] if len(parts) > 4 else ""
    if h < 2:
        while lenrem < lenadd:
            idx = s.rfind(" ", 0, lenrem)
            if idx > -1:
                p = cut(idx + 1, rec)
                out.append(p[0])
                curlength += idx + 1
                do_print()
                rec = p[1]
                parts = rec.split(",", 4)
                lenadd = int(parts[1])
                s = parts[4] if len(parts) > 4 else ""
                lenrem = linelength
            else:
                break
    if lenadd > linelength and lenrem:
        p = cut(lenrem, rec)
        out.append(p[0])
        curlength += lenrem
        do_print()
        rec = p[1]
    do_print()
    while get_length(rec) > linelength:
        p = cut(linelength, rec)
        out[:] = [p[0]]
        do_print()
        rec = p[1]
    curlength = 0
    return rec


def commit(rec: str):
    global curlength, out, chunks, level, wait, action
    debug_log(f"commit: rec={rec[:50]}...")
    if len(level) == 1:
        l = get_length(rec)
        if curlength + l > linelength:
            rec = prepare_cut(rec)
            l = get_length(rec)
        curlength += l
    out.append(rec)
    if len(out) - 1 != chunks[-1]:
        chunks.append(len(out) - 1)
    if len(level) > 1 and wait[len(level) - 1] == len(chunks) - level[len(level) - 1]:
        sub = action[len(level) - 1]
        debug_log(f"commit: triggering action '{sub}'")
        if sub == "":
            finish(wait[len(level) - 1])
        else:
            callsub(sub)


def uncommit() -> str:
    global curlength, out
    if not out:
        return empty()
    if len(level) == 1:
        curlength -= get_length(out[-1])
    rec = out[-1]
    out[-1] = empty()
    return rec


def finish(event, force_one_group: bool = False):
    global out, chunks, level, wait, action, tokenByToken, curlength
    debug_log(f"finish: event={event}, force={force_one_group}")
    if len(level) <= 1:
        return
    if len(out) < chunks[level[-1]]:
        out.append(empty())
    chunks[:] = chunks[: level[-1] + 1]
    t = []
    if len(level) == 2 and not force_one_group:
        t = out[chunks[-1] :]
        out = out[: chunks[-1]]
    level.pop()
    action.pop()
    tokenByToken.pop()
    wait.pop()
    if len(level) == 1 and not force_one_group:
        for rec in t:
            commit(rec)
    if len(level) > 1 and wait[-1] == len(chunks) - level[-1]:
        sub = action[-1]
        if sub == "":
            finish(wait[-1])
        else:
            callsub(sub)


def finish_ignore(event):
    global out, chunks, level, wait, action, tokenByToken
    if len(level) <= 1:
        return
    out[:] = out[: chunks[level[-1]]]
    level.pop()
    tokenByToken.pop()
    action.pop()
    wait.pop()


def start(event, act: str = ""):
    global chunks, level, wait, action, tokenByToken
    debug_log(f"start: event={event}, action={act}")
    if chunks[level[-1]] <= len(out) - 1 and chunks[-1] <= len(out) - 1:
        chunks.append(len(out))
    level.append(len(chunks) - 1)
    tokenByToken.append(0)
    wait.append(event)
    action.append(act)


def assertHave(n: int) -> bool:
    have = len(chunks) - level[-1]
    debug_log(f"assertHave: need={n}, have={have}")
    return have >= n


def collapse(n: int):
    global chunks, out
    have = len(chunks) - level[-1]
    debug_log(f"collapse: n={n}, have={have}")
    if have < n:
        n = have
    if n > 0:
        for i in range(n):
            collapseOne(len(chunks) - 1 - i)
        for i in range(1, n):
            chunks[len(chunks) - i] = chunks[len(chunks) - n] + n - i


def collapseAll():
    collapse(len(chunks) - level[-1])


def collapseOne(n: int):
    global out
    if n >= len(chunks):
        return
    if n == len(chunks) - 1:
        last = len(out) - 1
    else:
        last = chunks[n + 1] - 1
    start_idx = chunks[n]
    debug_log(f"collapseOne: n={n}, start={start_idx}, last={last}")
    if last <= start_idx:
        return
    result = out[start_idx]
    for i in range(start_idx + 1, last + 1):
        result = join_records(result, out[i])
    out[start_idx : last + 1] = [result]


def trim_end(idx: int):
    global out
    parts = out[idx].split(",", 4)
    h = int(parts[0])
    s = parts[4] if len(parts) > 4 else ""
    if not h:
        s = s.rstrip()
        out[idx] = string2record(s)


def trim_beg(idx: int):
    global out
    parts = out[idx].split(",", 4)
    h = int(parts[0])
    s = parts[4] if len(parts) > 4 else ""
    if not h:
        s = s.lstrip()
        out[idx] = string2record(s)


def trim_one(n: int):
    global out, chunks
    trim_beg(chunks[n])
    if n == len(chunks) - 1:
        trim_end(len(out) - 1)
    else:
        trim_end(chunks[n + 1] - 1)


def trim(n: int):
    debug_log(f"trim: n={n}")
    for i in range(len(chunks) - n, len(chunks)):
        trim_one(i)


def finishBuffer():
    global level
    while len(level) > 1:
        finish("")
    do_print(True)


def puts(s: str, no_expand: bool = False):
    commit(string2record(s, no_expand))


def callsub(sub: str):
    if ";" in sub:
        parts = sub.split(";", 1)
        name, arg = parts[0], parts[1]
        globals()[name](arg)
    else:
        globals()[sub]()


def get_balanced() -> Optional[str]:
    global par
    match = re.match(tokenpattern, par)
    if not match:
        return None
    tok = match.group(0)
    par = par[len(tok) :]
    if tok != "{":
        return tok
    result = ""
    lev = 1
    while lev and par:
        m = re.match(r"[^\\{}]|\\.|[{}]", par)
        if not m:
            break
        ch = m.group(0)
        par = par[len(ch) :]
        if ch == "{":
            lev += 1
        elif ch == "}":
            lev -= 1
        if lev:
            result += ch
    return result


def open_curly():
    start("}")


def close_curly():
    finish("}")


def dollar():
    global par
    if len(wait) > 1 and wait[-1] == "$":
        trim_end(len(out) - 1)
        finish("$")
    else:
        start("$")
        par = par.lstrip()


def ddollar():
    global par, out, chunks, level, tokenByToken, curlength
    if len(wait) > 1 and wait[-1] == "$$":
        trim_end(len(out) - 1)
        finish("$$")
        if len(out) > 0:
            chunks[:] = [0]
            trim(1)
            collapse(1)
            printrecord(center(linelength, out[0]))
            level[:] = [0]
            chunks[:] = [0]
            tokenByToken[:] = [0]
            out[:] = []
            curlength = 0
    else:
        finishBuffer()
        start("$$")
    par = par.lstrip()


def bbackslash():
    global par
    if len(wait) > 1 and wait[-1] == "$$":
        ddollar()
        ddollar()
    elif len(wait) > 1 and wait[-1] == "endCell":
        if re.match(r"\s*\\end", par):
            return
        finish("endCell", True)
        trim(1)
        collapse(1)
        finish("endRow", True)
        start("endRow")
        start("endCell")
    else:
        do_par()


def ampersand():
    if len(wait) > 1 and wait[-1] == "endCell":
        finish("endCell", True)
        trim(1)
        collapse(1)
        start("endCell")


def matrix():
    start("endMatrix")
    start("endRow")
    start("endCell")


def endmatrix(args_str: str = "1;c"):
    finish("endCell", True)
    trim(1)
    collapse(1)
    finish("endRow", True)
    halign(*args_str.split(";"))
    finish("endMatrix", True)


def endmatrixArg(args_str: str):
    global argStack
    arg = argStack.pop() if argStack else ""
    endmatrix(args_str + ";" + ";".join(arg))


def halign(explength_str: str, *c_args):
    global out, chunks, level
    explength = int(explength_str) if explength_str else 1
    c = list(c_args) if c_args else []
    w = []
    num_rows = len(chunks) - level[-1]
    for r in range(num_rows):
        if r == num_rows - 1:
            last = len(out) - 1
        else:
            last = chunks[r + 1 + level[-1]] - 1
        num_cols = last - chunks[r + level[-1]] + 1
        for col in range(num_cols):
            idx = chunks[r + level[-1]] + col
            l = get_length(out[idx])
            while len(w) <= col:
                w.append(0)
            if l > w[col]:
                w[col] = l
    for i in range(len(w) - 1):
        w[i] += explength
    if not c:
        c = ["c"] * len(w)
    while len(c) < len(w):
        c.append(c[-1] if c else "c")
    for r in range(num_rows):
        if r == num_rows - 1:
            last = len(out) - 1
        else:
            last = chunks[r + 1 + level[-1]] - 1
        num_cols = last - chunks[r + level[-1]] + 1
        for col in range(num_cols):
            idx = chunks[r + level[-1]] + col
            if col < len(w):
                if c[col] == "c":
                    out[idx] = center(w[col], out[idx])
                elif c[col] == "l":
                    pad = w[col] - get_length(out[idx])
                    out[idx] = join_records(out[idx], string2record(" " * pad))
                elif c[col] == "r":
                    pad = w[col] - explength - get_length(out[idx])
                    out[idx] = join_records(string2record(" " * pad), out[idx])
                    out[idx] = join_records(out[idx], string2record(" " * explength))
    collapseAll()
    base_idx = chunks[level[-1]]
    for i in range(base_idx + 1, len(out)):
        out[base_idx] = vStack(out[base_idx], out[i])
    h = get_height(out[base_idx])
    out[base_idx] = setbaseline(out[base_idx], (h - 1) // 2)
    chunks[:] = chunks[: level[-1] + 1]
    out[:] = out[: base_idx + 1]


def subscript():
    start(1, "f_subscript")
    tokenByToken[-1] = 1


def superscript():
    start(1, "f_superscript")
    tokenByToken[-1] = 1


def f_subscript():
    global par
    wait[-1] = 2
    action[-1] = "f_subSuper"
    if not re.match(r"\s*\^", par) and not re.match(r"\s*\\begin\s*\{Sp\}", par):
        commit(empty())
    else:
        par = re.sub(r"^\s*\^", "", par)
        par = re.sub(r"^\s*\\begin\s*\{Sp\}", r"\\begin{matrix}", par)


def f_superscript():
    global par
    wait[-1] = 2
    action[-1] = "f_superSub"
    if not re.match(r"\s*_", par) and not re.match(r"\s*\\begin\s*\{Sb\}", par):
        commit(empty())
    else:
        par = re.sub(r"^\s*_", "", par)
        par = re.sub(r"^\s*\\begin\s*\{Sb\}", r"\\begin{matrix}", par)


def f_subSuper():
    trim(2)
    collapse(2)
    if not assertHave(2):
        finish("", True)
        return
    sup_sub(0, 1)


def f_superSub():
    trim(2)
    collapse(2)
    if not assertHave(2):
        finish("", True)
        return
    sup_sub(1, 0)


def sup_sub(p1_off: int, p2_off: int):
    global out, chunks
    p1 = len(out) - 1 - p1_off
    p2 = len(out) - 1 - p2_off
    parts1 = out[p1].split(",", 4)
    parts2 = out[p2].split(",", 4)
    h1, l1 = int(parts1[0]) or 1, int(parts1[1])
    h2, l2 = int(parts2[0]) or 1, int(parts2[1])
    str1 = parts1[4] if len(parts1) > 4 else ""
    str2 = parts2[4] if len(parts2) > 4 else ""
    if l1 == 0 and l2 == 0:
        finish(2, True)
        return
    l = max(l1, l2)
    chunks.pop()
    out.pop()
    if l1 == 0:
        h = h2 + 1
        out[-1] = f"{h},{l},0,0,\n{str2}"
    elif l2 == 0:
        h = h1 + 1
        out[-1] = f"{h},{l},{h1},0,{str1}\n"
    else:
        h = h1 + h2 + 1
        out[-1] = f"{h},{l},{h1},0,{str1}\n\n{str2}"
    finish(2, True)


def f_fraction():
    global out, chunks
    debug_log(f"f_fraction called")
    trim(2)
    collapse(2)
    if not assertHave(2):
        debug_log("f_fraction: not enough chunks")
        finish("", True)
        return
    numer = out[-2]
    denom = out[-1]
    debug_log(f"f_fraction: numer={numer}, denom={denom}")
    l1, l2 = get_length(numer), get_length(denom)
    length = max(l1, l2)
    numer_centered = center(length, numer)
    denom_centered = center(length, denom)
    line_rec = string2record("─" * length)
    result = vStack(vStack(numer_centered, line_rec), denom_centered)
    numer_h = get_height(numer_centered)
    result = setbaseline(result, numer_h)
    debug_log(f"f_fraction: result={result}")
    out[-2] = result
    chunks.pop()
    out.pop()
    finish(2, True)


def f_choose():
    global out, chunks
    trim(2)
    collapse(2)
    if not assertHave(2):
        finish("", True)
        return
    l1, l2 = get_length(out[-2]), get_length(out[-1])
    length = max(l1, l2)
    out[-1] = vStack(
        vStack(center(length, out[-2]), string2record(" " * length)),
        center(length, out[-1]),
    )
    chunks.append(len(out))
    out.append(empty())
    out[-3] = string2record("(")
    out[-1] = string2record(")")
    parts = out[-2].split(",", 4)
    h, b = int(parts[0]), int(parts[2])
    makehigh_inplace(-3, h, b, 0, 1)
    makehigh_inplace(-1, h, b, 1, 0)
    finish(2, True)


def f_radical():
    global out
    trim(1)
    collapse(1)
    if not assertHave(1):
        finish("", True)
        return
    parts = out[-1].split(",", 4)
    h, l, b = int(parts[0]) or 1, int(parts[1]), int(parts[2])
    content = parts[4] if len(parts) > 4 else ""
    lines = content.split("\n") if content else [""]
    while len(lines) < h:
        lines.append("")

    # Top bar with closing corner: " ┌───┐"
    result_lines = [" ┌" + "─" * l + "┐"]

    for i in range(h):
        line_padded = lines[i].ljust(l)  # Ensure content fills width
        if i == h - 1:
            result_lines.append("⟍│" + line_padded + " ")
        else:
            result_lines.append(" │" + line_padded + " ")

    new_h = h + 1
    new_l = l + 3  # 2 for prefix ("⟍│" or " ┌"), 1 for suffix ("┐" or " ")
    new_b = b + 1
    out[-1] = f"{new_h},{new_l},{new_b},0," + "\n".join(result_lines)
    finish(1, True)


def f_overline():
    global out
    trim(1)
    collapse(1)
    if not assertHave(1):
        finish("", True)
        return
    parts = out[-1].split(",", 4)
    h, l, b = int(parts[0]) or 1, int(parts[1]), int(parts[2])
    out[-1] = vStack(string2record("_" * l), out[-1])
    out[-1] = setbaseline(out[-1], b + 1)
    finish(1, True)


def f_underline():
    global out
    trim(1)
    collapse(1)
    if not assertHave(1):
        finish("", True)
        return
    parts = out[-1].split(",", 4)
    h, l, b = int(parts[0]) or 1, int(parts[1]), int(parts[2])
    out[-1] = vStack(out[-1], string2record("_" * l))
    out[-1] = setbaseline(out[-1], b)
    finish(1, True)


def f_not():
    global out
    collapse(1)
    if not assertHave(1):
        finish("", True)
        return
    parts = out[-1].split(",", 4)
    s = parts[4] if len(parts) > 4 else ""
    if s == "=":
        out[-1] = contents.get("\\neq", string2record("≠"))
    elif s.strip() == "|":
        out[-1] = contents.get("\\nmid", string2record("∤"))
    elif out[-1] == contents.get("\\in"):
        out[-1] = contents.get("\\notin", string2record("∉"))
    else:
        out[-1] = join_records(string2record("\\not"), out[-1])
    finish(1, True)


def f_putover(rec: str, no_finish: bool = False):
    global out
    trim(1)
    collapse(1)
    if not assertHave(1):
        finish("", True)
        return
    parts = out[-1].split(",", 4)
    h, l1, b = int(parts[0]) or 1, int(parts[1]), int(parts[2])
    l2 = get_length(rec)
    length = max(l1, l2)
    parts_rec = rec.split(",", 4)
    b1 = int(parts_rec[0]) or 1
    b += b1 + 1
    out[-1] = vStack(center(length, rec), center(length, out[-1]))
    out[-1] = setbaseline(out[-1], b)
    if not no_finish:
        finish(1, True)


def f_putunder(rec: str):
    global out
    trim(1)
    collapse(1)
    if not assertHave(1):
        finish("", True)
        return
    parts = out[-1].split(",", 4)
    h, l1, b = int(parts[0]) or 1, int(parts[1]), int(parts[2])
    l2 = get_length(rec)
    length = max(l1, l2)
    out[-1] = vStack(center(length, out[-1]), center(length, rec))
    out[-1] = setbaseline(out[-1], b)
    finish(1, True)


def f_putover_string(s: str):
    f_putover(string2record(s))


def f_widehat():
    trim(1)
    collapse(1)
    l = get_length(out[-1])
    if l <= 1:
        f_putover(string2record("^"))
    else:
        f_putover(string2record("/" + "~" * (l - 2) + "\\"))


def f_widetilde():
    trim(1)
    collapse(1)
    l = get_length(out[-1])
    if l <= 1:
        f_putover(string2record("~"))
    elif l <= 3:
        f_putover(string2record("/\\/"))
    else:
        l1 = l // 2 - 1
        f_putover(string2record("/" + "~" * l1 + "\\" + "_" * (l - 3 - l1) + "/"))


def f_putpar(delims: str):
    global out
    trim(1)
    l, r = delims.split(";")
    collapse(1)
    if not assertHave(1):
        finish("", True)
        return
    out[-1] = join_records(string2record(l), join_records(out[-1], string2record(r)))
    finish(1, True)


def f_buildrel():
    global out, chunks
    trim(3)
    collapse(3)
    if not assertHave(3):
        finish("", True)
        return
    rec = out[-3]
    out[-3] = out[-1]
    chunks[:] = chunks[:-2]
    out[:] = out[:-2]
    f_putover(rec, True)
    finish(3, True)


def left():
    start(3, "f_leftright")
    tokenByToken[-1] = 1
    start(1, "f_left")
    tokenByToken[-1] = 1


def f_left():
    trim(1)
    collapse(1)
    finish(1)
    start("LeftRight")


def right():
    finish("LeftRight", True)
    trim(1)
    collapse(1)


def f_leftright():
    global out
    trim(1)
    collapse(1)
    if not assertHave(3):
        return
    parts = out[-2].split(",", 4)
    h, b = int(parts[0]) or 1, int(parts[2])

    # Check if we're dealing with square brackets
    left_parts = out[-3].split(",", 4)
    left_s = left_parts[4] if len(left_parts) > 4 else ""
    right_parts = out[-1].split(",", 4)
    right_s = right_parts[4] if len(right_parts) > 4 else ""

    # For square brackets, ensure minimum height of 3 for visual clarity
    # This makes single-row matrices display with content in the middle row
    # so that "B(t) =" aligns with the content, not the bottom bracket
    if left_s == "[" and right_s == "]" and h < 3:
        content_str = parts[4] if len(parts) > 4 else ""
        l = int(parts[1])
        sp = int(parts[3])

        if h <= 1:
            # Single line content -> put in middle row
            lines = [" " * l, content_str.ljust(l) if content_str else " " * l, " " * l]
            new_b = 1
        else:  # h == 2
            old_lines = content_str.split("\n") if content_str else ["", ""]
            while len(old_lines) < 2:
                old_lines.append("")

            # h=2 with b=0 typically means superscript case (halign sets b=(h-1)//2=0)
            # Row 0 is superscript, row 1 is main content
            # Keep superscript on top, main content in middle, add empty row at bottom
            # Baseline should point to main content (row 1 after expansion)
            lines = [old_lines[0].ljust(l), old_lines[1].ljust(l), " " * l]
            new_b = 1  # points to main content row

        out[-2] = f"3,{l},{new_b},{sp}," + "\n".join(lines)
        h, b = 3, new_b

    debug_log(f"f_leftright: h={h}, b={b}, out[-3]={out[-3][:80]}")
    debug_log(f"f_leftright: out[-2]={out[-2][:80]}")
    debug_log(f"f_leftright: out[-1]={out[-1][:80]}")

    makehigh_inplace(-3, h, b, 0, 1)
    makehigh_inplace(-1, h, b, 1, 0)
    finish(3)


def beg_lr(delims: str):
    start(1, f"f_leftright_go;{delims}")
    tokenByToken[-1] = 1


def f_leftright_go(delims: str):
    global out
    trim(1)
    collapse(1)
    l, r = delims.split(";")
    if not assertHave(1):
        return
    rec = out[-1]
    out.pop()
    wait[-1] = "junk"
    start(3, "f_leftright")
    puts(l)
    commit(rec)
    puts(r)
    finish("junk")


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
    if ascent >= 1 and descent > 0 and exp_real == middle:
        return top + exp_real * (ascent + descent - 2) + bottom
    if descent <= 0:
        return exp_one * (ascent - 1) + base
    if ascent <= 1:
        return base + exp_one * descent
    above = top + exp_real * (ascent - 2) if ascent >= 2 else top
    below = exp_real * (descent - 1) + bottom if descent > 1 else bottom
    return above + middle + below


def makehigh_inplace(idx: int, h: int, b: int, left_sp: int, right_sp: int):
    global out
    parts = out[idx].split(",", 4)
    s = parts[4] if len(parts) > 4 else ""
    debug_log(
        f"makehigh_inplace: idx={idx}, h={h}, b={b}, left_sp={left_sp}, right_sp={right_sp}, s='{s}'"
    )
    if s == ".":
        out[idx] = f"{parts[0]},{parts[1]},{parts[2]},{parts[3]}, "
        return
    h = h if h > 0 else 1
    d = h - b - 1
    if h < 2 or (h == 2 and s in "()<>"):
        return
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
        c = ["|", "|", "|", "|", "|", "|"]
    elif s == "[":
        c = ["[", " ", "│", "┌", "└", "│"]
    elif s == "]":
        c = ["]", " ", "│", "┐", "┘", "│"]
    elif s in ("<", ">"):
        if h == 2:
            return

        # Calculate width needed
        max_dist = max(b, h - b - 1)  # max distance from baseline
        width = max_dist + 1

        result_lines = []
        for row in range(h):
            dist_from_baseline = abs(row - b)

            if s == "<":
                # Tip on left, slants go right
                col = dist_from_baseline
                if row < b:
                    char = "⧸"
                elif row == b:
                    char = "⟨"
                else:
                    char = "⧹"
            else:  # ">"
                # Tip on right, slants go left
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
    compound = makecompound(b + 1, d, *c)
    out[idx] = vputs(compound, b)
    if len(s) == 2:
        out[idx] = join_records(out[idx], out[idx])
    if left_sp:
        out[idx] = join_records(string2record(" " * left_sp), out[idx])
    if right_sp:
        out[idx] = join_records(out[idx], string2record(" " * right_sp))


def over():
    global out, chunks
    if len(wait) > 1 and wait[-1] == "}":
        prevw = wait[-2]
        wait[-2] = "junk"
        finish("}", True)
        collapse(1)
        if not assertHave(1):
            finish("", True)
            return
        rec = out[-1]
        out.pop()
        chunks.pop()
        start(2, "f_fraction")
        wait[-2] = prevw
        start("}")
        commit(rec)
        finish("}", True)
        start("}")
    else:
        puts("\\over")


def choose():
    global out, chunks
    if len(wait) > 1 and wait[-1] == "}":
        prevw = wait[-2]
        wait[-2] = "junk"
        finish("}", True)
        collapse(1)
        if not assertHave(1):
            finish("", True)
            return
        rec = out[-1]
        out.pop()
        chunks.pop()
        start(2, "f_choose")
        wait[-2] = prevw
        start("}")
        commit(rec)
        finish("}", True)
        start("}")
    else:
        puts("\\choose")


def noindent():
    global out, chunks
    if len(out) == 1 and len(chunks) == 1 and out[0] == "1,5,0,0,     ":
        out.pop()
        chunks.pop()
    else:
        puts("\\noindent")


def item():
    finishBuffer()
    commit("1,11,0,0,     (@)   ")


def at():
    global par
    if not par:
        puts("@")
        return
    c = par[0]
    if c == "@":
        puts("@")
        par = par[1:]
    elif c in "<>AV":
        m = ""
        if len(wait) > 1 and wait[-1] == "endCell":
            m = "&"
        if m == "&" and c in "AV":
            m = "&&"
        if m == "&":
            ampersand()
        par = par[1:]
        first, second = "", ""
        while True:
            t = get_balanced()
            if t is None or t == c:
                break
            first += t
        while True:
            t = get_balanced()
            if t is None or t == c:
                break
            second += t
        par = "{" + first + "}{" + second + "}" + m + par
        l_tip = c.replace("A", "^").replace(">", "")
        r_tip = c.replace("<", "").replace("A", "")
        if c in "<>":
            start(2, f"f_arrow;{l_tip};{r_tip}")
        else:
            start(2, f"f_arrow_v;{l_tip};{r_tip}")
    elif c == "." and len(wait) > 1 and wait[-1] == "endCell":
        ampersand()
        ampersand()
        par = par[1:]
    else:
        puts("@")


def f_arrow(tips: str):
    global out, chunks
    l, r = tips.split(";")
    trim(2)
    collapse(2)
    if not assertHave(2):
        finish("", True)
        return
    l1, l2 = get_length(out[-2]), get_length(out[-1])
    length = max(l1, l2)
    out[-2] = vStack(
        vStack(
            center(length + 4, out[-2]),
            string2record(f" {l}" + "-" * (length + 1) + f"{r} "),
        ),
        center(length + 4, out[-1]),
    )
    chunks.pop()
    out.pop()
    finish(2, True)


def f_arrow_v(tips: str):
    global out, chunks
    l, r = tips.split(";")
    trim(2)
    collapse(2)
    if not assertHave(2):
        finish("", True)
        return
    parts1 = out[-2].split(",", 4)
    parts2 = out[-1].split(",", 4)
    h1, b1 = int(parts1[0]) or 1, int(parts1[2])
    h2, b2 = int(parts2[0]) or 1, int(parts2[2])
    b = max(b1, b2)
    res = join_records(out[-2], out[-1])
    parts = res.split(",", 4)
    h = int(parts[0]) or 1
    bb = b + 1
    out[-2] = vStack(vputs(" " * (b - b1 + 1)), out[-2])
    out[-2] = setbaseline(out[-2], bb)
    out[-1] = vStack(vputs(" " * (b - b2 + 1)), out[-1])
    out[-1] = setbaseline(out[-1], bb)
    out[-2] = join_records(
        join_records(out[-2], vputs(l + "|" * (h + 1) + r, b + 1)), out[-1]
    )
    chunks.pop()
    out.pop()
    finish(2, True)


def do_par():
    global par
    finishBuffer()
    if not re.match(r"^\s*\\noindent\s*(\s+|[^a-zA-Z\s]|$)", par):
        commit("1,5,0,0,     ")
    else:
        par = re.sub(r"^\s*\\noindent\s*(\s+|([^a-zA-Z\s])|$)", r"\2", par)


def f_begin():
    collapse(1)
    if not assertHave(1):
        finish("")
        return
    rec = f_get1()
    finish_ignore(1)
    arg = rec.strip()
    if arg in environment_none:
        return
    if arg in environment:
        env = environment[arg]
        b, e = env.split(",", 1) if "," in env else (env, "")
        for sub in b.split(":"):
            if sub:
                callsub(sub)
    else:
        puts(f"\\begin{{{arg}}}")


def f_end():
    collapse(1)
    if not assertHave(1):
        finish("")
        return
    rec = f_get1()
    finish_ignore(1)
    arg = rec.strip()
    if arg in environment_none:
        return
    if arg in environment:
        env = environment[arg]
        parts = env.split(",", 1)
        e = parts[1] if len(parts) > 1 else ""
        for sub in e.split(":"):
            if sub:
                callsub(sub)
    else:
        puts(f"\\end{{{arg}}}")


def f_get1() -> str:
    global out
    if len(out) - 1 != chunks[-1]:
        return ""
    parts = out[-1].split(",", 4)
    return parts[4] if len(parts) > 4 else ""


def f_discard():
    finish_ignore(wait[-1])


def f_literal_no_length():
    collapse(1)
    if not assertHave(1):
        finish("", True)
        return
    out[-1] = record_forcelength(out[-1], 0)
    finish(1, True)


def arg2stack():
    global argStack
    arg = get_balanced()
    if arg:
        argStack.append(arg)


def let_cmd():
    global par
    match = re.match(f"({tokenpattern})(= ?)?({tokenpattern})", par)
    if match:
        par = par[len(match.group(0)) :]


def let_exp():
    global par
    match = re.match(f"({tokenpattern})(= ?)?({tokenpattern})", par)
    if match:
        par = par[len(match.group(0)) :]
        if "@" in match.group(0):
            return
        what = match.group(1)
        last_match = re.search(f"({tokenpattern})$", match.group(0))
        if last_match:
            type_table[what] = "def"
            defs[what] = last_match.group(1)
            args[what] = 0


def def_cmd():
    global par
    par = re.sub(r"^[^{]*", "", par)
    start(1, "f_discard")
    tokenByToken[-1] = 1


def def_exp():
    global par
    match = re.match(r"(([^\\{]|\\.)*)\{", par)
    if not match:
        return
    arg = match.group(1)
    par = par[len(match.group(0)) - 1 :]
    definition = get_balanced()
    if definition is None:
        return
    if "@" in arg + definition:
        return
    if re.search(r"\\([egx]?def|fi)([^a-zA-Z]|$)", definition):
        return
    if re.search(f"({macro})$", definition):
        definition += " "
    define(arg, definition)


def define(arg: str, definition: str):
    match = re.match(f"^({active})", arg)
    if not match:
        return
    act = match.group(1)
    rest = arg[len(act) :]
    if not re.match(r"^(#\d)*$", rest):
        return
    args[act] = len(rest) // 2
    defs[act] = definition
    type_table[act] = "def"


def defb(*names):
    for name in names:
        define(f"\\{name}", f"\\begin{{{name}}}")
        define(f"\\end{name}", f"\\end{{{name}}}")


def init_symbols():
    global type_table, contents, environment, environment_none

    type_table["\\sum"] = "record"
    contents["\\sum"] = "3,3,1,0,__ \n❯  \n‾‾ "
    type_table["\\int"] = "record"
    contents["\\int"] = "3,2,1,0, ╭\n |\n ╯"
    type_table["\\oint"] = "record"
    contents["\\oint"] = "3,2,1,0, ╭\n ⦶\n ╯"
    type_table["\\prod"] = "record"
    contents["\\prod"] = "2,3,1,0,___\n│ │"
    type_table["\\Sigma"] = "record"
    contents["\\Sigma"] = "3,2,1,0,__\n❯ \n‾‾"

    greek = {
        "\\alpha": "α",
        "\\beta": "β",
        "\\gamma": "γ",
        "\\delta": "δ",
        "\\epsilon": "ε",
        "\\zeta": "ζ",
        "\\eta": "η",
        "\\theta": "θ",
        "\\iota": "ι",
        "\\kappa": "κ",
        "\\lambda": "λ",
        "\\mu": "μ",
        "\\nu": "ν",
        "\\xi": "ξ",
        "\\pi": "π",
        "\\rho": "ρ",
        "\\sigma": "σ",
        "\\tau": "τ",
        "\\upsilon": "υ",
        "\\phi": "φ",
        "\\chi": "χ",
        "\\psi": "ψ",
        "\\omega": "ω",
        "\\Gamma": "Γ",
        "\\Delta": "△",
        "\\Theta": "Θ",
        "\\Lambda": "Λ",
        "\\Xi": "Ξ",
        "\\Pi": "π",
        "\\Upsilon": "Υ",
        "\\Phi": "Φ",
        "\\Psi": "Ψ",
        "\\Omega": "Ω",
    }
    for k, v in greek.items():
        type_table[k] = "string"
        contents[k] = v

    strings = {
        "\\,": " ",
        "\\;": " ",
        "\\|": "||",
        "\\approx": " ≅ ",
        "\\backslash": "\\",
        "\\bullet": "•",
        "\\cap": " ∩ ",
        "\\cdot": " · ",
        "\\cdots": "⋯",
        "\\circ": " o ",
        "\\colon": ": ",
        "\\cong": "≅",
        "\\cup": " ∪ ",
        "\\dots": "...",
        "\\equiv": " ≡ ",
        "\\exists": " ∃",
        "\\forall": " ∀",
        "\\from": " <── ",
        "\\ge": " ≥ ",
        "\\geq": " ≥ ",
        "\\hbar": "ℏ",
        "\\hookleftarrow": " ↩ ",
        "\\hookrightarrow": " ↪ ",
        "\\in": " ∈ ",
        "\\infty": "∞",
        "\\ldots": "...",
        "\\Leftarrow": " <== ",
        "\\leftarrow": " <── ",
        "\\leftrightarrow": " <──> ",
        "\\le": " ≤ ",
        "\\leq": " ≤ ",
        "\\lhd": " ⊲ ",
        "\\longleftarrow": " <──── ",
        "\\longleftrightarrow": " <────> ",
        "\\longmapsto": " ├────> ",
        "\\longrightarrow": " ────> ",
        "\\ltimes": "⋉",
        "\\mapsto": " ├──> ",
        "\\mid": " | ",
        "\\mp": " ∓ ",
        "\\nabla": "∇",        
        "\\ne": " ≠ ",
        "\\neq": " ≠ ",
        "\\ni": " ∌ ",
        "\\nmid": " ∤ ",
        "\\notin": " ∉ ",
        "\\ominus": " ⊖ ",
        "\\oplus": " ⊕ ",
        "\\otimes": " ⊗ ",
        "\\owns": " ∋ ",
        "\\partial": "∂",
        "\\pm": " ± ",
        "\\qed": "∎",
        "\\qquad": "     ",
        "\\quad": "   ",
        "\\rhd": " ⊳ ",
        "\\Rightarrow": " ==> ",
        "\\rightarrow": " ──> ",
        "\\rtimes": " ⋊ ",
        "\\section": "Section ",
        "\\setminus": " ⧹ ",
        "\\simeq": " ≃ ",
        "\\smallsetminus": " ⧵ ",
        "\\subsection": "Subsection ",
        "\\subset": " ⊂ ",
        "\\subseteq": " ⊆ ",
        "\\supset": " ⊃ ",
        "\\supseteq": " ⊇ ",
        "\\textit": " ",
        "\\times": " × ",
        "\\to": " ──> ",
        "\\vee": " ∨ ",
        "\\wedge": " ∧ ",
        "~": " ",
    }
    for k, v in strings.items():
        type_table[k] = "string"
        contents[k] = v

    for cmd in [
        "@",
        "_",
        "$",
        "{",
        "}",
        "#",
        "&",
        "arccos",
        "arcsin",
        "arctan",
        "arg",
        "cos",
        "cosh",
        "cot",
        "coth",
        "csc",
        "deg",
        "det",
        "dim",
        "exp",
        "gcd",
        "hom",
        "inf",
        "ker",
        "lg",
        "lim",
        "liminf",
        "limsup",
        "ln",
        "log",
        "max",
        "min",
        "mod",
        "Pr",
        "sec",
        "sin",
        "sinh",
        "sup",
        "tan",
        "tanh",
        "%",
    ]:
        type_table[f"\\{cmd}"] = "self"

    for cmd in [
        "mathcal",
    ]:
        type_table[f"\\{cmd}"] = "fancy"

    for cmd in [
        "mathbf",
    ]:
        type_table[f"\\{cmd}"] = "bold"

    for cmd in [
        "mathit",
    ]:
        type_table[f"\\{cmd}"] = "italic"

    for cmd in [
        "text",
        "operatorname",
        "operatornamewithlimits",
        "relax",
        "-",
        "notag",
        "!",
        "/",
        "protect",
        "Bbb",
        "bf",
        "it",
        "em",
        "boldsymbol",
        "cal",
        "Cal",
        "goth",
        "ref",
        "maketitle",
        "expandafter",
        "csname",
        "endcsname",
        "makeatletter",
        "makeatother",
        "topmatter",
        "endtopmatter",
        "rm",
        "NoBlackBoxes",
        "document",
        "TagsOnRight",
        "bold",
        "dsize",
        "roster",
        "endroster",
        "endkey",
        "endRefs",
        "enddocument",
        "displaystyle",
        "twelverm",
        "tenrm",
        "twelvefm",
        "tenfm",
        "hbox",
        "mbox",
    ]:
        type_table[f"\\{cmd}"] = "nothing"

    for cmd in [
        "par",
        "endtitle",
        "endauthor",
        "endaffil",
        "endaddress",
        "endemail",
        "endhead",
        "key",
        "medskip",
        "smallskip",
        "bigskip",
        "newpage",
        "vfill",
        "eject",
        "endgraph",
    ]:
        type_table[f"\\{cmd}"] = "sub"
        contents[f"\\{cmd}"] = "do_par"

    for cmd in ["proclaim", "demo"]:
        type_table[f"\\{cmd}"] = "par_self"

    for cmd in ["endproclaim", "enddemo"]:
        type_table[f"\\{cmd}"] = "self_par"

    for cmd in [
        "bibliography",
        "myLabel",
        "theoremstyle",
        "theorembodyfont",
        "bibliographystyle",
        "hphantom",
        "vphantom",
        "phantom",
        "hspace",
    ]:
        type_table[f"\\{cmd}"] = "discard1"

    for cmd in ["numberwithin", "newtheorem", "renewcommand", "setcounter"]:
        type_table[f"\\{cmd}"] = "discard2"

    type_table["\\let"] = "sub"
    contents["\\let"] = "let_exp"
    type_table["\\def"] = "sub"
    contents["\\def"] = "def_exp"
    type_table["\\item"] = "sub"
    contents["\\item"] = "item"
    type_table["{"] = "sub"
    contents["{"] = "open_curly"
    type_table["}"] = "sub"
    contents["}"] = "close_curly"
    type_table["&"] = "sub"
    contents["&"] = "ampersand"
    type_table["$"] = "sub"
    contents["$"] = "dollar"
    type_table["$$"] = "sub"
    contents["$$"] = "ddollar"
    type_table["\\\\"] = "sub"
    contents["\\\\"] = "bbackslash"
    type_table["@"] = "sub"
    contents["@"] = "at"
    type_table["\\over"] = "sub"
    contents["\\over"] = "over"
    type_table["\\choose"] = "sub"
    contents["\\choose"] = "choose"
    type_table["\\noindent"] = "sub"
    contents["\\noindent"] = "noindent"
    type_table["\\left"] = "sub"
    contents["\\left"] = "left"
    type_table["\\right"] = "sub"
    contents["\\right"] = "right"

    sub1_cmds = {
        "\\sqrt": "radical",
        "\\underline": "underline",
        "\\overline": "overline",
        "\\bar": "overline",
        "\\v": "putover_string;v",
        "\\widetilde": "widetilde",
        "\\~": "putover_string;~",
        "\\tilde": "putover_string;~",
        "\\widehat": "widehat",
        "\\hat": "putover_string;^",
        "\\^": "putover_string;^",
        '\\"': 'putover_string;"',
        "\\dot": "putover_string;.",
        "\\not": "not",
        "\\label": "putpar;(;)",
        "\\eqref": "putpar;(;)",
        "\\cite": "putpar;[;]",
        "\\begin": "begin",
        "\\end": "end",
        "\\LITERALnoLENGTH": "literal_no_length",
    }
    for k, v in sub1_cmds.items():
        type_table[k] = "sub1"
        contents[k] = v

    type_table["\\frac"] = "sub2"
    contents["\\frac"] = "fraction"

    type_table["^"] = "sub1"
    contents["^"] = "superscript"
    type_table["_"] = "sub1"
    contents["_"] = "subscript"

    type_table["\\buildrel"] = "sub3"
    contents["\\buildrel"] = "buildrel"

    for env in ["equation", "gather", "align"]:
        environment[env] = "ddollar,ddollar"

    for env in ["matrix", "CD", "smallmatrix"]:
        environment[env] = "matrix,endmatrix;1;c"

    for env in ["document", "split", "enumerate"]:
        environment_none[env] = True

    environment["Sb"] = "subscript:matrix,endmatrix;1;l"
    environment["Sp"] = "superscript:matrix,endmatrix;1;l"
    environment["eqnarray"] = "ddollar:matrix,endmatrix;0;r;c;l:ddollar"
    environment["split"] = "ddollar:matrix,endmatrix;0;r;l:ddollar"
    environment["multiline"] = "ddollar:matrix,endmatrix;0;r;l:ddollar"
    environment["align"] = "ddollar:matrix,endmatrix;0;r;l:ddollar"
    environment["aligned"] = "matrix,endmatrix;0;r;l"
    environment["gather"] = "ddollar:matrix,endmatrix;0;c:ddollar"
    environment["gathered"] = "matrix,endmatrix;0;c"
    environment["array"] = "arg2stack:matrix,endmatrixArg;1"
    environment["bmatrix"] = "beg_lr;[;]:matrix,endmatrix;1;c"
    environment["vmatrix"] = "beg_lr;|;|:matrix,endmatrix;1;c"

    if opt_TeX:
        define("\\pmatrix#1", "\\left(\\begin{matrix}#1\\end{matrix}\\right)")
    else:
        environment["pmatrix"] = "beg_lr;(;):matrix,endmatrix;1;c"

    for op in ["oplus", "otimes", "cup", "wedge"]:
        type_table[f"\\big{op}"] = type_table.get(f"\\{op}", "string")
        contents[f"\\big{op}"] = contents.get(f"\\{op}", "")

    define("\\define", "\\def")
    define("\\ge", "\\geq")
    define("\\le", "\\leq")
    define("\\ne", "\\neq")
    define("\\langle", "<")
    define("\\rangle", ">")
    define("\\subheading", "\\par\\underline")
    define("\\(", "$")
    define("\\)", "$")
    define("\\[", "$$")
    define("\\]", "$$")
    define("\\centerline#1", "$$#1$$")
    define("\\eqalign#1", "\\aligned #1 \\endaligned")
    define("\\cr", "\\\\")
    define("\\sb", "_")
    define("\\sp", "^")
    define("\\proclaim", "\\noindent ")

    defb(
        "matrix",
        "vmatrix",
        "Vmatrix",
        "smallmatrix",
        "bmatrix",
        "Sp",
        "Sb",
        "CD",
        "align",
        "aligned",
        "split",
        "multiline",
        "gather",
        "gathered",
    )

    for k in list(contents.keys()):
        if type_table.get(k) == "record" and contents[k].endswith("\n"):
            contents[k] = contents[k][:-1]

def make_text_fancy(input_text:str) -> str:
    result = []
    for char in input_text:
        if 'A' <= char <= 'Z':
            script_map = {
                'A': '𝒜', 'B': '𝐵', 'C': '𝒞', 'D': '𝒟',
                'E': '𝐸', 'F': '𝐹', 'G': '𝒢', 'H': '𝐻',
                'I': '𝐼', 'J': '𝒥', 'K': '𝒦', 'L': '𝐿',
                'M': '𝑀', 'N': '𝒩', 'O': '𝒪', 'P': '𝒫',
                'Q': '𝒬', 'R': '𝑅', 'S': '𝒮', 'T': '𝒯',
                'U': '𝒰', 'V': '𝒱', 'W': '𝒲', 'X': '𝒳',
                'Y': '𝒴', 'Z': '𝒵'
            }
            result.append(script_map.get(char, char))
        elif 'a' <= char <= 'z':
            script_map = {
                'a': '𝒶', 'b': '𝒷', 'c': '𝒸', 'd': '𝒹',
                'e': '𝑒', 'f': '𝒻', 'g': '𝑔', 'h': '𝒽',
                'i': '𝒾', 'j': '𝒿', 'k': '𝓀', 'l': '𝓁',
                'm': '𝓂', 'n': '𝓃', 'o': '𝑜', 'p': '𝓅',
                'q': '𝓆', 'r': '𝓇', 's': '𝓈', 't': '𝓉',
                'u': '𝓊', 'v': '𝓋', 'w': '𝓌', 'x': '𝓍',
                'y': '𝓎', 'z': '𝓏'
            }
            result.append(script_map.get(char, char))
        else:
            result.append(char)
    return ''.join(result)

def make_text_bold(text_input: str) -> str:
    result = []
    for char in text_input:
        if 'A' <= char <= 'Z':
            script_map = {
                'A': '𝐀', 'B': '𝐁', 'C': '𝐂', 'D': '𝐃',
                'E': '𝐄', 'F': '𝐅', 'G': '𝐆', 'H': '𝐇',
                'I': '𝐈', 'J': '𝐉', 'K': '𝐊', 'L': '𝐋',
                'M': '𝐌', 'N': '𝐍', 'O': '𝐎', 'P': '𝐏',
                'Q': '𝐐', 'R': '𝐑', 'S': '𝐒', 'T': '𝐓',
                'U': '𝐔', 'V': '𝐕', 'W': '𝐖', 'X': '𝐗',
                'Y': '𝐘', 'Z': '𝐙'
            }
            result.append(script_map.get(char, char))
        elif 'a' <= char <= 'z':
            script_map = {
                'a': '𝐚', 'b': '𝐛', 'c': '𝐜', 'd': '𝐝',
                'e': '𝐞', 'f': '𝐟', 'g': '𝐠', 'h': '𝐡',
                'i': '𝐢', 'j': '𝐣', 'k': '𝐤', 'l': '𝐥',
                'm': '𝐦', 'n': '𝐧', 'o': '𝐨', 'p': '𝐩',
                'q': '𝐪', 'r': '𝐫', 's': '𝐬', 't': '𝐭',
                'u': '𝐮', 'v': '𝐯', 'w': '𝐰', 'x': '𝐱',
                'y': '𝐲', 'z': '𝐳'
            }
            result.append(script_map.get(char, char))
        elif '0' <= char <= '9':
            # Mathematical bold digits
            script_map = {
                '0': '𝟎', '1': '𝟏', '2': '𝟐', '3': '𝟑',
                '4': '𝟒', '5': '𝟓', '6': '𝟔', '7': '𝟕',
                '8': '𝟖', '9': '𝟗'
            }
            result.append(script_map.get(char, char))
        else:
            result.append(char)
    return ''.join(result)

def make_text_italic(text_input: str) -> str:
    result = []
    for char in text_input:
        if 'A' <= char <= 'Z':
            script_map = {
                'A': '𝐴', 'B': '𝐵', 'C': '𝐶', 'D': '𝐷',
                'E': '𝐸', 'F': '𝐹', 'G': '𝐺', 'H': '𝐻',
                'I': '𝐼', 'J': '𝐽', 'K': '𝐾', 'L': '𝐿',
                'M': '𝑀', 'N': '𝑁', 'O': '𝑂', 'P': '𝑃',
                'Q': '𝑄', 'R': '𝑅', 'S': '𝑆', 'T': '𝑇',
                'U': '𝑈', 'V': '𝑉', 'W': '𝑊', 'X': '𝑋',
                'Y': '𝑌', 'Z': '𝑍'
            }
            result.append(script_map.get(char, char))
        elif 'a' <= char <= 'z':
            script_map = {
                'a': '𝑎', 'b': '𝑏', 'c': '𝑐', 'd': '𝑑',
                'e': '𝑒', 'f': '𝑓', 'g': '𝑔', 'h': 'ℎ',
                'i': '𝑖', 'j': '𝑗', 'k': '𝑘', 'l': '𝑙',
                'm': '𝑚', 'n': '𝑛', 'o': '𝑜', 'p': '𝑝',
                'q': '𝑞', 'r': '𝑟', 's': '𝑠', 't': '𝑡',
                'u': '𝑢', 'v': '𝑣', 'w': '𝑤', 'x': '𝑥',
                'y': '𝑦', 'z': '𝑧'
            }
            result.append(script_map.get(char, char))
        else:
            result.append(char)
    return ''.join(result)

def paragraph(input_text: str) -> bool:
    global par, secondtime, out, chunks, level, tokenByToken, curlength, argStack
    par = input_text
    if not par:
        return False
    if not re.search(r"\S", par):
        return True
    match = re.search(r"\\begin\{document\}", par)
    if match:
        par = par[match.start() :]
    if secondtime and not opt_by_par:
        print()
    secondtime += 1
    par = re.sub(r"((^|[^\\])(\\\\)*)(%.*\n[ \t]*)+", r"\1", par, flags=re.MULTILINE)
    par = re.sub(r"\n\s*\n", r"\\par ", par)
    par = re.sub(r"\s+", " ", par)
    par = par.rstrip()
    par = re.sub(r"(\$\$)\s+", r"\1", par)
    par = re.sub(r"\\par\s*$", "", par)
    defcount = 0
    if not opt_noindent and not re.match(r"^\s*\\noindent\s*([^a-zA-Z\s]|$)", par):
        commit("1,5,0,0,     ")
    else:
        par = re.sub(r"^\s*\\noindent\s*([^a-zA-Z\s]|$)", r"\1", par)
    token_re = re.compile(tokenpattern if tokenByToken[-1] else multitokenpattern)
    while par:
        par = par.lstrip() if not tokenByToken[-1] else par
        match = token_re.match(par)
        if not match:
            break
        piece = match.group(0)
        par = par[len(piece) :]
        if re.match(usualtokenclass, piece):
            # Add leading space before binary operators in math mode
            in_math = len(wait) > 1 and any(
                w in ("$", "$$", "}", "LeftRight", "endCell") for w in wait
            )
            if in_math and piece and piece[0] in "+-=":
                puts(" " + piece)
            else:
                puts(piece)
        else:
            pure = piece.rstrip()
            typ = type_table.get(pure)
            debug_log(f"token: '{pure}' type={typ}")
            if typ == "def":
                defcount += 1
                if defcount > maxdef:
                    break
                t = [""]
                for i in range(1, args.get(pure, 0) + 1):
                    t.append(get_balanced() or "")
                sub = defs.get(pure, "")
                if args.get(pure, 0):
                    for i in range(args[pure], 0, -1):
                        sub = re.sub(f"([^\\\\#])#{i}", f"\\1{t[i]}", sub)
                        sub = re.sub(f"^#{i}", t[i], sub)
                par = sub + par
            elif typ == "sub":
                sub = contents.get(pure, "")
                if ";" in sub:
                    parts = sub.split(";", 1)
                    globals()[parts[0]](pure, parts[1])
                elif sub:
                    globals()[sub]()
            elif typ and typ.startswith("sub") and typ[3:].isdigit():
                n = int(typ[3:])
                func_name = f"f_{contents.get(pure, '')}"
                debug_log(f"sub{n} command '{pure}' -> {func_name}")
                start(n, func_name)
                tokenByToken[-1] = 1
            elif typ and typ.startswith("get"):
                n = int(typ[3:])
                start(n + 1)
                puts(piece)
                tokenByToken[-1] = 1
            elif typ and typ.startswith("discard"):
                n = int(typ[7:])
                start(n, "f_discard")
                tokenByToken[-1] = 1
            elif typ == "record":
                commit(contents.get(pure, empty()))
            elif typ == "self":
                #suffix = " " if re.match(r"^\\[a-zA-Z]", pure) else ""
                suffix = ""
                puts(pure[1:] + suffix)
            elif typ == "fancy":
                text = get_balanced()
                puts(make_text_fancy(text))
            elif typ == "bold":
                text = get_balanced()
                puts(make_text_bold(text))
            elif typ == "italic":
                text = get_balanced()
                puts(make_text_italic(text))
            elif typ == "par_self":
                finishBuffer()
                commit("1,5,0,0,     ")
                suffix = " " if re.match(r"^\\[a-zA-Z]", pure) else ""
                puts(pure + suffix)
            elif typ == "self_par":
                suffix = " " if re.match(r"^\\[a-zA-Z]", pure) else ""
                puts(pure + suffix)
                finishBuffer()
                if not re.match(r"^\s*\\noindent(\s+|[^a-zA-Z\s]|$)", par):
                    commit("1,5,0,0,     ")
                else:
                    par = re.sub(r"^\s*\\noindent(\s+|([^a-zA-Z\s])|$)", r"\2", par)
            elif typ == "string":
                content = contents.get(pure, "")
                # Avoid double spacing: if content starts with space and
                # the last output ends with space, strip our leading space
                if content.startswith(" ") and out:
                    last_parts = out[-1].split(",", 4)
                    last_s = last_parts[4] if len(last_parts) > 4 else ""
                    if last_s.endswith(" "):
                        content = content[1:]  # remove leading space
                puts(content, True)
            elif typ == "nothing":
                pass
            else:
                puts(piece)
        token_re = re.compile(tokenpattern if tokenByToken[-1] else multitokenpattern)
    if out:
        finishBuffer()
    return True


def main():
    global linelength, opt_by_par, opt_TeX, opt_ragged, opt_noindent, opt_debug
    parser = argparse.ArgumentParser(description="Convert TeX/LaTeX to UTF-8 text")
    parser.add_argument("filename", help="Input TeX file")
    parser.add_argument("--linelength", type=int, default=150)
    parser.add_argument("--ragged", action="store_true")
    parser.add_argument("--noindent", action="store_true")
    parser.add_argument("--by_par", action="store_true")
    parser.add_argument("--TeX", action="store_true", default=True)
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    args = parser.parse_args()
    linelength = args.linelength
    opt_by_par = args.by_par
    opt_TeX = args.TeX
    opt_ragged = args.ragged
    opt_noindent = args.noindent
    opt_debug = args.debug
    init_symbols()
    try:
        with open(args.filename, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: File '{args.filename}' not found", file=sys.stderr)
        sys.exit(1)
    if opt_by_par:
        paragraphs = content.split("\n\n")
        for p in paragraphs:
            paragraph(p)
    else:
        paragraph(content)
    finishBuffer()


if __name__ == "__main__":
    main()
