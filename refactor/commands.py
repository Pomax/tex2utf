"""
LaTeX command handlers for tex2utf.

This module contains handler functions for LaTeX commands and
special characters. Each handler is responsible for processing
a specific command or character sequence.

Handler Types:
--------------
1. Simple handlers (e.g., open_curly, dollar):
   Called directly when their trigger is encountered.

2. Argument-collecting handlers (e.g., subscript, superscript):
   Start a group to collect arguments, then call a completion function.

3. Environment handlers (f_begin, f_end):
   Process \\begin{env} and \\end{env} commands.

Command Registration:
---------------------
Commands are registered in symbols.py which populates:
- state.type_table: Maps command -> handler type
- state.contents: Maps command -> handler name or content

Special Characters Handled:
---------------------------
- { } : Grouping braces
- $ $$ : Math mode delimiters
- ^ _ : Super/subscript
- & : Column separator (in matrices)
- \\\\ : Row separator
- @ : Commutative diagram arrows
"""

import re

from .config import debug_log, tokenpattern
from .records import empty, string2record, get_length, get_height, setbaseline, center
from .join import join_records
from .brackets import makehigh_inplace
from . import state
from . import stack
from . import math_ops


def get_balanced():
    """
    Get a balanced group from the input.

    If the next token is '{', reads until the matching '}'.
    Otherwise, returns just the next token.

    This is used to read macro arguments.

    Returns:
        The content of the group (without braces), or None if no token
    """
    match = re.match(tokenpattern, state.par)
    if not match:
        return None
    tok = match.group(0)
    state.par = state.par[len(tok):]
    if tok != "{":
        return tok

    # Read until matching }
    result = ""
    lev = 1
    while lev and state.par:
        m = re.match(r"[^\\{}]|\\.|[{}]", state.par)
        if not m:
            break
        ch = m.group(0)
        state.par = state.par[len(ch):]
        if ch == "{":
            lev += 1
        elif ch == "}":
            lev -= 1
        if lev:
            result += ch
    return result


def open_curly():
    """Handle opening curly brace - start a new group."""
    stack.start("}")


def close_curly():
    """Handle closing curly brace - finish the current group."""
    stack.finish("}")


def dollar():
    """
    Handle single dollar sign - toggle inline math mode.

    If already in $...$ mode, closes it. Otherwise, opens it.
    """
    if len(state.wait) > 1 and state.wait[-1] == "$":
        stack.trim_end(len(state.out) - 1)
        stack.finish("$")
    else:
        stack.start("$")
        state.par = state.par.lstrip()


def ddollar():
    """
    Handle double dollar sign - toggle display math mode.

    Display math is centered on its own line.
    """
    from . import config
    from .output import printrecord

    if len(state.wait) > 1 and state.wait[-1] == "$$":
        # Closing display math
        stack.trim_end(len(state.out) - 1)
        stack.finish("$$")
        if len(state.out) > 0:
            state.chunks[:] = [0]
            stack.trim(1)
            stack.collapse(1)
            # Center the display math
            printrecord(center(config.linelength, state.out[0]))
            # Reset state
            state.level[:] = [0]
            state.chunks[:] = [0]
            state.tokenByToken[:] = [0]
            state.out[:] = []
            state.curlength = 0
    else:
        # Opening display math
        stack.finishBuffer()
        stack.start("$$")
    state.par = state.par.lstrip()


def bbackslash():
    """
    Handle \\\\ (backslash-backslash) - line/row break.

    In display math: ends the equation
    In matrices/tables: ends the current row
    Otherwise: paragraph break
    """
    if len(state.wait) > 1 and state.wait[-1] == "$$":
        ddollar()
        ddollar()
    elif len(state.wait) > 1 and state.wait[-1] == "endCell":
        if re.match(r"\s*\\end", state.par):
            return
        stack.finish("endCell", True)
        stack.trim(1)
        stack.collapse(1)
        stack.finish("endRow", True)
        stack.start("endRow")
        stack.start("endCell")
    else:
        do_par()


def ampersand():
    """
    Handle & - column separator in matrices and tables.

    Finishes the current cell and starts a new one.
    """
    if len(state.wait) > 1 and state.wait[-1] == "endCell":
        stack.finish("endCell", True)
        stack.trim(1)
        stack.collapse(1)
        stack.start("endCell")


def matrix():
    """
    Start a matrix environment.

    Sets up nested groups for: matrix > rows > cells
    """
    stack.start("endMatrix")
    stack.start("endRow")
    stack.start("endCell")


def endmatrix(args_str: str = "1;c"):
    """
    End a matrix environment and format the result.

    Args:
        args_str: "spacing;alignments" where alignments is column specs
                  e.g., "1;c" for centered, "1;l;r" for left,right
    """
    stack.finish("endCell", True)
    stack.trim(1)
    stack.collapse(1)
    stack.finish("endRow", True)
    halign(*args_str.split(";"))
    stack.finish("endMatrix", True)


def endmatrixArg(args_str: str):
    """End matrix with alignment from argument stack."""
    arg = state.argStack.pop() if state.argStack else ""
    endmatrix(args_str + ";" + ";".join(arg))


def halign(explength_str: str, *c_args):
    """
    Perform horizontal alignment of matrix columns.

    Calculates column widths and aligns content according to
    the specified alignment characters (l, c, r).

    Args:
        explength_str: Extra spacing between columns
        *c_args: Column alignment specifiers ('l', 'c', 'r')
    """
    from .records import vStack

    explength = int(explength_str) if explength_str else 1
    c = list(c_args) if c_args else []
    w = []  # Column widths

    # Calculate column widths
    num_rows = len(state.chunks) - state.level[-1]
    for r in range(num_rows):
        if r == num_rows - 1:
            last = len(state.out) - 1
        else:
            last = state.chunks[r + 1 + state.level[-1]] - 1
        num_cols = last - state.chunks[r + state.level[-1]] + 1
        for col in range(num_cols):
            idx = state.chunks[r + state.level[-1]] + col
            l = get_length(state.out[idx])
            while len(w) <= col:
                w.append(0)
            if l > w[col]:
                w[col] = l

    # Add inter-column spacing
    for i in range(len(w) - 1):
        w[i] += explength

    # Default to center alignment
    if not c:
        c = ["c"] * len(w)
    while len(c) < len(w):
        c.append(c[-1] if c else "c")

    # Apply alignment to each cell
    for r in range(num_rows):
        if r == num_rows - 1:
            last = len(state.out) - 1
        else:
            last = state.chunks[r + 1 + state.level[-1]] - 1
        num_cols = last - state.chunks[r + state.level[-1]] + 1
        for col in range(num_cols):
            idx = state.chunks[r + state.level[-1]] + col
            if col < len(w):
                if c[col] == "c":
                    state.out[idx] = center(w[col], state.out[idx])
                elif c[col] == "l":
                    pad = w[col] - get_length(state.out[idx])
                    state.out[idx] = join_records(state.out[idx], string2record(" " * pad))
                elif c[col] == "r":
                    pad = w[col] - explength - get_length(state.out[idx])
                    state.out[idx] = join_records(string2record(" " * pad), state.out[idx])
                    state.out[idx] = join_records(state.out[idx], string2record(" " * explength))

    # Collapse all rows, then stack vertically
    stack.collapseAll()
    base_idx = state.chunks[state.level[-1]]
    for i in range(base_idx + 1, len(state.out)):
        state.out[base_idx] = vStack(state.out[base_idx], state.out[i])

    # Set baseline to middle
    h = get_height(state.out[base_idx])
    state.out[base_idx] = setbaseline(state.out[base_idx], (h - 1) // 2)
    state.chunks[:] = state.chunks[: state.level[-1] + 1]
    state.out[:] = state.out[: base_idx + 1]


def subscript():
    """Start collecting subscript content."""
    stack.start(1, "f_subscript")
    state.tokenByToken[-1] = 1


def superscript():
    """Start collecting superscript content."""
    stack.start(1, "f_superscript")
    state.tokenByToken[-1] = 1


def over():
    """
    Handle \\over command (TeX-style fraction).

    Syntax: {numerator \\over denominator}
    """
    if len(state.wait) > 1 and state.wait[-1] == "}":
        prevw = state.wait[-2]
        state.wait[-2] = "junk"
        stack.finish("}", True)
        stack.collapse(1)
        if not stack.assertHave(1):
            stack.finish("", True)
            return
        rec = state.out[-1]
        state.out.pop()
        state.chunks.pop()
        stack.start(2, "f_fraction")
        state.wait[-2] = prevw
        stack.start("}")
        stack.commit(rec)
        stack.finish("}", True)
        stack.start("}")
    else:
        stack.puts("\\over")


def choose():
    """
    Handle \\choose command (binomial coefficient).

    Syntax: {n \\choose k}
    """
    if len(state.wait) > 1 and state.wait[-1] == "}":
        prevw = state.wait[-2]
        state.wait[-2] = "junk"
        stack.finish("}", True)
        stack.collapse(1)
        if not stack.assertHave(1):
            stack.finish("", True)
            return
        rec = state.out[-1]
        state.out.pop()
        state.chunks.pop()
        stack.start(2, "f_choose")
        state.wait[-2] = prevw
        stack.start("}")
        stack.commit(rec)
        stack.finish("}", True)
        stack.start("}")
    else:
        stack.puts("\\choose")


def noindent():
    """Handle \\noindent - suppress paragraph indentation."""
    if len(state.out) == 1 and len(state.chunks) == 1 and state.out[0] == "1,5,0,0,     ":
        state.out.pop()
        state.chunks.pop()
    else:
        stack.puts("\\noindent")


def item():
    """Handle \\item - enumeration item."""
    stack.finishBuffer()
    stack.commit("1,11,0,0,     (@)   ")


def at():
    """
    Handle @ command - commutative diagram arrows.

    Syntax:
    - @>>> : Right arrow
    - @<<< : Left arrow
    - @VVV : Down arrow
    - @AAA : Up arrow
    - @. : Empty cell
    """
    if not state.par:
        stack.puts("@")
        return
    c = state.par[0]
    if c == "@":
        stack.puts("@")
        state.par = state.par[1:]
    elif c in "<>AV":
        m = ""
        if len(state.wait) > 1 and state.wait[-1] == "endCell":
            m = "&"
        if m == "&" and c in "AV":
            m = "&&"
        if m == "&":
            ampersand()
        state.par = state.par[1:]
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
        state.par = "{" + first + "}{" + second + "}" + m + state.par
        l_tip = c.replace("A", "^").replace(">", "")
        r_tip = c.replace("<", "").replace("A", "")
        if c in "<>":
            stack.start(2, f"f_arrow;{l_tip};{r_tip}")
        else:
            stack.start(2, f"f_arrow_v;{l_tip};{r_tip}")
    elif c == "." and len(state.wait) > 1 and state.wait[-1] == "endCell":
        ampersand()
        ampersand()
        state.par = state.par[1:]
    else:
        stack.puts("@")


def do_par():
    """Handle paragraph break."""
    stack.finishBuffer()
    if not re.match(r"^\s*\\noindent\s*(\s+|[^a-zA-Z\s]|$)", state.par):
        stack.commit("1,5,0,0,     ")
    else:
        state.par = re.sub(r"^\s*\\noindent\s*(\s+|([^a-zA-Z\s])|$)", r"\2", state.par)


def left():
    """
    Handle \\left delimiter.

    Starts collection of: left_delim, content, right_delim
    The delimiters will be scaled to match content height.
    """
    stack.start(3, "f_leftright")
    state.tokenByToken[-1] = 1
    stack.start(1, "f_left")
    state.tokenByToken[-1] = 1


def f_left():
    """Process left delimiter after collection."""
    stack.trim(1)
    stack.collapse(1)
    stack.finish(1)
    stack.start("LeftRight")


def right():
    """Handle \\right delimiter - closes \\left...\\right pair."""
    stack.finish("LeftRight", True)
    stack.trim(1)
    stack.collapse(1)


def f_leftright():
    """
    Complete \\left...\\right pair processing.

    Scales delimiters to match content height and joins them.
    """
    stack.trim(1)
    stack.collapse(1)
    if not stack.assertHave(3):
        return
    parts = state.out[-2].split(",", 4)
    h, b = int(parts[0]) or 1, int(parts[2])

    left_parts = state.out[-3].split(",", 4)
    left_s = left_parts[4] if len(left_parts) > 4 else ""
    right_parts = state.out[-1].split(",", 4)
    right_s = right_parts[4] if len(right_parts) > 4 else ""

    if left_s == "[" and right_s == "]" and h < 3:
        content_str = parts[4] if len(parts) > 4 else ""
        l = int(parts[1])
        sp = int(parts[3])

        if h <= 1:
            lines = [" " * l, content_str.ljust(l) if content_str else " " * l, " " * l]
            new_b = 1
        else:
            old_lines = content_str.split("\n") if content_str else ["", ""]
            while len(old_lines) < 2:
                old_lines.append("")
            lines = [old_lines[0].ljust(l), old_lines[1].ljust(l), " " * l]
            new_b = 1

        state.out[-2] = f"3,{l},{new_b},{sp}," + "\n".join(lines)
        h, b = 3, new_b

    debug_log(f"f_leftright: h={h}, b={b}, out[-3]={state.out[-3][:80]}")
    debug_log(f"f_leftright: out[-2]={state.out[-2][:80]}")
    debug_log(f"f_leftright: out[-1]={state.out[-1][:80]}")

    makehigh_inplace(state.out, -3, h, b, 0, 1)
    makehigh_inplace(state.out, -1, h, b, 1, 0)
    stack.finish(3)


def beg_lr(delims: str):
    """Begin left-right pair with specific delimiters (for environments)."""
    stack.start(1, f"f_leftright_go;{delims}")
    state.tokenByToken[-1] = 1


def f_leftright_go(delims: str):
    """Process environment-based left-right delimiters."""
    stack.trim(1)
    stack.collapse(1)
    l, r = delims.split(";")
    if not stack.assertHave(1):
        return
    rec = state.out[-1]
    state.out.pop()
    state.wait[-1] = "junk"
    stack.start(3, "f_leftright")
    stack.puts(l)
    stack.commit(rec)
    stack.puts(r)
    stack.finish("junk")


def do_matrix():
    """Handle \\matrix command (TeX-style matrix)."""
    arg = get_balanced()
    if arg:
        state.par = "\\begin{matrix}" + arg + "\\end{matrix}" + state.par


def f_begin():
    """
    Handle \\begin{environment} command.

    Looks up the environment in state.environment and calls
    the appropriate begin handlers.
    """
    stack.collapse(1)
    if not stack.assertHave(1):
        stack.finish("")
        return
    rec = f_get1()
    stack.finish_ignore(1)
    arg = rec.strip()
    if arg in state.environment_none:
        return
    if arg in state.environment:
        env = state.environment[arg]
        b, e = env.split(",", 1) if "," in env else (env, "")
        for sub in b.split(":"):
            if sub:
                stack.callsub(sub)
    else:
        stack.puts(f"\\begin{{{arg}}}")


def f_end():
    """
    Handle \\end{environment} command.

    Calls the appropriate end handlers for the environment.
    """
    stack.collapse(1)
    if not stack.assertHave(1):
        stack.finish("")
        return
    rec = f_get1()
    stack.finish_ignore(1)
    arg = rec.strip()
    if arg in state.environment_none:
        return
    if arg in state.environment:
        env = state.environment[arg]
        parts = env.split(",", 1)
        e = parts[1] if len(parts) > 1 else ""
        for sub in e.split(":"):
            if sub:
                stack.callsub(sub)
    else:
        stack.puts(f"\\end{{{arg}}}")


def f_trig_function(func_name: str):
    """
    Handle trigonometric functions (sin, cos, etc.).

    Outputs the function name and wraps the argument in parentheses
    if it's a braced group.

    Args:
        func_name: The function name without backslash
    """
    # Skip whitespace
    state.par = state.par.lstrip()

    if not state.par:
        stack.puts(func_name)
        return

    # Check if already has parentheses via \left( or just (
    if state.par.startswith("\\left"):
        stack.puts(func_name)
        return  # Let normal processing handle it
    if state.par.startswith("("):
        # Already parenthesized - output function name directly attached to the paren
        # Find matching closing paren
        level = 0
        i = 0
        for i, ch in enumerate(state.par):
            if ch == "(":
                level += 1
            elif ch == ")":
                level -= 1
                if level == 0:
                    break
        # Extract the parenthesized expression including parens
        paren_expr = state.par[:i+1]
        state.par = state.par[i+1:]
        stack.puts(func_name + paren_expr)
        return

    # Output the function name
    stack.puts(func_name)

    # Check if followed by a LaTeX command
    if state.par.startswith("\\"):
        match = re.match(r"^\\([a-zA-Z]+)", state.par)
        if match:
            cmd_name = "\\" + match.group(1)
            cmd_type = state.type_table.get(cmd_name)
            # If it's a simple string replacement (like \theta -> θ), wrap it
            if cmd_type == "string":
                full_match = re.match(r"^(\\[a-zA-Z]+)\s*", state.par)
                state.par = state.par[len(full_match.group(0)):]
                stack.puts("(" + state.contents.get(cmd_name, cmd_name[1:]) + ")")
                return
            # For all other command types (sub1, sub2, sub3, record, def, etc.),
            # let normal processing handle it without parentheses
            return

    # Get the next argument (braced group or single token)
    if state.par.startswith("{"):
        arg = get_balanced()
        if arg is not None:
            stack.puts("(")
            old_par = state.par
            state.par = arg
            while state.par:
                if not parser.paragraph(state.par):
                    break
            state.par = old_par
            stack.puts(")")
    elif re.match(r"^\\[a-zA-Z]+", state.par):
        match = re.match(r"^(\\[a-zA-Z]+)\s*", state.par)
        if match:
            macro_text = match.group(1)
            state.par = state.par[len(match.group(0)):]
            stack.puts("(")
            old_par = state.par
            state.par = macro_text
            while state.par:
                if not parser.paragraph(state.par):
                    break
            state.par = old_par
            stack.puts(")")
    elif re.match(r"^[a-zA-Z0-9]", state.par):
        # Single letter/digit
        arg = state.par[0]
        state.par = state.par[1:]
        stack.puts("(" + arg + ")")


def f_get1() -> str:
    """Get the text content of the last output record."""
    if len(state.out) - 1 != state.chunks[-1]:
        return ""
    parts = state.out[-1].split(",", 4)
    return parts[4] if len(parts) > 4 else ""


def f_discard():
    """Discard the current group (for commands that consume but ignore args)."""
    stack.finish_ignore(state.wait[-1])


def arg2stack():
    """Push a balanced argument onto the argument stack."""
    arg = get_balanced()
    if arg:
        state.argStack.append(arg)


def let_cmd():
    """Handle \\let in command mode (just consume the syntax)."""
    match = re.match(f"({tokenpattern})(= ?)?({tokenpattern})", state.par)
    if match:
        state.par = state.par[len(match.group(0)):]


def let_exp():
    """Handle \\let in expansion mode (create an alias)."""
    match = re.match(f"({tokenpattern})(= ?)?({tokenpattern})", state.par)
    if match:
        state.par = state.par[len(match.group(0)):]
        if "@" in match.group(0):
            return
        what = match.group(1)
        last_match = re.search(f"({tokenpattern})$", match.group(0))
        if last_match:
            state.type_table[what] = "def"
            state.defs[what] = last_match.group(1)
            state.args[what] = 0


def def_cmd():
    """Handle \\def in command mode (just consume it)."""
    state.par = re.sub(r"^[^{]*", "", state.par)
    stack.start(1, "f_discard")
    state.tokenByToken[-1] = 1


def def_exp():
    """Handle \\def in expansion mode (define a macro)."""
    from .config import macro

    match = re.match(r"(([^\\{]|\\.)*)\{", state.par)
    if not match:
        return
    arg = match.group(1)
    state.par = state.par[len(match.group(0)) - 1:]
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
    """
    Define a macro.

    Args:
        arg: Macro name and parameter spec (e.g., "\\foo#1#2")
        definition: Replacement text with #1, #2, etc.
    """
    from .config import active

    match = re.match(f"^({active})", arg)
    if not match:
        return
    act = match.group(1)
    rest = arg[len(act):]
    if not re.match(r"^(#\d)*$", rest):
        return
    state.args[act] = len(rest) // 2
    state.defs[act] = definition
    state.type_table[act] = "def"


def defb(*names):
    """Define \\name and \\endname as begin/end shortcuts."""
    for name in names:
        define(f"\\{name}", f"\\begin{{{name}}}")
        define(f"\\end{name}", f"\\end{{{name}}}")
