"""
Token parsing and paragraph processing for tex2utf.

This module contains the main parsing loop that tokenizes LaTeX
input and dispatches to appropriate handlers.

Parsing Process:
----------------
1. Preprocess input (remove comments, normalize whitespace)
2. Tokenize using regex patterns from config.py
3. For each token:
   - Look up in type_table to find handler type
   - Dispatch to appropriate handler
   - Handler may modify state.par to inject new content
4. After all tokens processed, flush output buffer

Token Types:
------------
- Usual tokens: Regular text characters (processed as-is)
- Active tokens: Special characters and macros
  - Macros: \\command sequences
  - Special: $, $$, {, }, ^, _, &, @, ~

Math Mode Handling:
-------------------
The parser tracks whether we're in math mode via state.wait.
In math mode:
- Spaces around operators (+, -, =) are added
- Differential notation (dx, dt) gets special spacing
"""

import re

from . import config
from . import state
from . import stack
from . import commands
from . import math_ops
from .config import debug_log, tokenpattern, multitokenpattern, usualtokenclass
from .text_transforms import make_text_fancy, make_text_bold, make_text_italic, make_text_double


def paragraph(input_text: str) -> bool:
    """
    Process a paragraph (or complete document) of LaTeX input.

    This is the main entry point for parsing. It handles:
    - Comment removal
    - Whitespace normalization
    - Tokenization
    - Command dispatch

    Args:
        input_text: Raw LaTeX input string

    Returns:
        True if processing was successful
    """
    state.par = input_text

    # Handle empty input
    if not state.par:
        return False
    if not re.search(r"\S", state.par):
        return True

    # Skip preamble - find \begin{document} if present
    match = re.search(r"\\begin\{document\}", state.par)
    if match:
        state.par = state.par[match.start():]

    # Add blank line between paragraphs (except first)
    if state.secondtime and not config.opt_by_par:
        print()
    state.secondtime += 1

    # =========================================================================
    # Preprocessing: Clean up the input
    # =========================================================================

    # Remove comments: % to end of line (but not escaped \%)
    # The pattern handles \\% (escaped backslash then percent)
    state.par = re.sub(r"((^|[^\\])(\\\\)*)(%.*\n[ \t]*)+", r"\1", state.par, flags=re.MULTILINE)

    # Convert double newlines (blank lines) to \par commands
    state.par = re.sub(r"\n\s*\n", r"\\par ", state.par)

    # Normalize all whitespace to single spaces
    state.par = re.sub(r"\s+", " ", state.par)
    state.par = state.par.rstrip()

    # Remove space after $$ (display math shouldn't have leading space)
    state.par = re.sub(r"(\$\$)\s+", r"\1", state.par)

    # Remove trailing \par (no need for final paragraph break)
    state.par = re.sub(r"\\par\s*$", "", state.par)

    # Counter to prevent infinite macro expansion loops
    defcount = 0

    # Add paragraph indentation (5 spaces) unless suppressed
    if not config.opt_noindent and not re.match(r"^\s*\\noindent\s*([^a-zA-Z\s]|$)", state.par):
        stack.commit("1,5,0,0,     ")
    else:
        state.par = re.sub(r"^\s*\\noindent\s*([^a-zA-Z\s]|$)", r"\1", state.par)

    # Choose token pattern based on current parsing mode
    # tokenByToken mode parses one token at a time (for collecting arguments)
    # Otherwise, we can grab multiple regular characters at once
    token_re = re.compile(tokenpattern if state.tokenByToken[-1] else multitokenpattern)

    # =========================================================================
    # Main Parsing Loop
    # =========================================================================
    while state.par:
        # Skip leading whitespace (unless in token-by-token mode)
        state.par = state.par.lstrip() if not state.tokenByToken[-1] else state.par

        # Match the next token
        match = token_re.match(state.par)
        if not match:
            break
        piece = match.group(0)
        state.par = state.par[len(piece):]

        # ---------------------------------------------------------------------
        # Handle regular text (usual token class)
        # ---------------------------------------------------------------------
        if re.match(usualtokenclass, piece):
            # Check if we're currently in math mode
            in_math = len(state.wait) > 1 and any(
                w in ("$", "$$", "}", "LeftRight", "endCell") for w in state.wait
            )

            if in_math and piece and piece[0] in "+-=":
                # Add space before operators in math mode for readability
                stack.puts(" " + piece)
            elif in_math:
                # Special handling for differential notation (dx, dt, dy, etc.)
                # These should have a thin space before them
                diff_match = re.search(r"d[txyzrsuvw]\s*$", piece)
                debug_log(f"checking diff in '{piece}': match={diff_match}")
                if diff_match and diff_match.start() > 0:
                    before = piece[:diff_match.start()]
                    diff = piece[diff_match.start():]
                    stack.puts(before)
                    # Don't add space after / (as in dx/dt)
                    if not before.endswith("/"):
                        stack.puts(" " + diff)
                    else:
                        stack.puts(diff)
                # Add space before ( when starting a new term
                elif piece.startswith("(") and len(state.out) > 0:
                    last_out = state.out[-1] if state.out else ""
                    last_char = (
                        last_out.rstrip().split("\n")[0][-1:]
                        if last_out.rstrip()
                        else ""
                    )
                    # Don't add space after operators or opening brackets
                    if last_char and last_char not in "+-=*/(<[{":
                        stack.puts(" " + piece)
                    else:
                        stack.puts(piece)
                else:
                    stack.puts(piece)
            else:
                # Not in math mode - just output the text
                stack.puts(piece)

        # ---------------------------------------------------------------------
        # Handle active tokens (commands and special characters)
        # ---------------------------------------------------------------------
        else:
            pure = piece.rstrip()  # Remove trailing whitespace from macro
            typ = state.type_table.get(pure)
            debug_log(f"token: '{pure}' type={typ}")

            # -----------------------------------------------------------------
            # User-defined macro expansion
            # -----------------------------------------------------------------
            if typ == "def":
                defcount += 1
                if defcount > config.maxdef:
                    break  # Prevent infinite expansion

                # Collect macro arguments
                t = [""]  # t[0] unused, t[1] = #1, t[2] = #2, etc.
                for i in range(1, state.args.get(pure, 0) + 1):
                    t.append(commands.get_balanced() or "")

                # Get the macro definition and substitute arguments
                sub = state.defs.get(pure, "")
                if state.args.get(pure, 0):
                    # Replace #n with argument n (in reverse order to handle #10 before #1)
                    for i in range(state.args[pure], 0, -1):
                        sub = re.sub(f"([^\\\\#])#{i}", f"\\1{t[i]}", sub)
                        sub = re.sub(f"^#{i}", t[i], sub)

                # Prepend expansion to input for further processing
                state.par = sub + state.par

            # -----------------------------------------------------------------
            # Simple subroutine call (no arguments)
            # -----------------------------------------------------------------
            elif typ == "sub":
                sub = state.contents.get(pure, "")
                if ";" in sub:
                    # Format: "function;arg" - call function with argument
                    parts = sub.split(";", 1)
                    func = getattr(commands, parts[0], None)
                    if func:
                        func(pure, parts[1])
                elif sub:
                    # Just a function name
                    func = getattr(commands, sub, None)
                    if func:
                        func()

            # -----------------------------------------------------------------
            # Subroutine with N arguments (sub1, sub2, sub3)
            # -----------------------------------------------------------------
            elif typ and typ.startswith("sub") and typ[3:].isdigit():
                n = int(typ[3:])
                func_name = f"f_{state.contents.get(pure, '')}"
                debug_log(f"sub{n} command '{pure}' -> {func_name}")
                # Start collecting n arguments, then call func_name
                stack.start(n, func_name)
                state.tokenByToken[-1] = 1  # Parse token-by-token for arguments

            # -----------------------------------------------------------------
            # Get command (outputs itself plus collects arguments)
            # -----------------------------------------------------------------
            elif typ and typ.startswith("get"):
                n = int(typ[3:])
                stack.start(n + 1)
                stack.puts(piece)
                state.tokenByToken[-1] = 1

            # -----------------------------------------------------------------
            # Discard command (consumes and ignores arguments)
            # -----------------------------------------------------------------
            elif typ and typ.startswith("discard"):
                n = int(typ[7:])
                stack.start(n, "f_discard")
                state.tokenByToken[-1] = 1

            # -----------------------------------------------------------------
            # Pre-built record (e.g., \sum, \int)
            # -----------------------------------------------------------------
            elif typ == "record":
                stack.commit(state.contents.get(pure, stack.empty()))

            # -----------------------------------------------------------------
            # Self-printing command (outputs its name without backslash)
            # -----------------------------------------------------------------
            elif typ == "self":
                suffix = ""
                stack.puts(pure[1:] + suffix)

            # -----------------------------------------------------------------
            # Trigonometric function (wraps argument in parentheses)
            # -----------------------------------------------------------------
            elif typ == "trig":
                commands.f_trig_function(pure[1:])

            # -----------------------------------------------------------------
            # Text style transformations
            # -----------------------------------------------------------------
            elif typ == "fancy":
                text = commands.get_balanced()
                stack.puts(make_text_fancy(text))
            elif typ == "bold":
                text = commands.get_balanced()
                stack.puts(make_text_bold(text))
            elif typ == "italic":
                text = commands.get_balanced()
                stack.puts(make_text_italic(text))
            elif typ == "double":
                text = commands.get_balanced()
                stack.puts(make_text_double(text))

            # -----------------------------------------------------------------
            # Paragraph + self-printing
            # -----------------------------------------------------------------
            elif typ == "par_self":
                stack.finishBuffer()
                stack.commit("1,5,0,0,     ")
                suffix = " " if re.match(r"^\\[a-zA-Z]", pure) else ""
                stack.puts(pure + suffix)
            elif typ == "self_par":
                suffix = " " if re.match(r"^\\[a-zA-Z]", pure) else ""
                stack.puts(pure + suffix)
                stack.finishBuffer()
                if not re.match(r"^\s*\\noindent(\s+|[^a-zA-Z\s]|$)", state.par):
                    stack.commit("1,5,0,0,     ")
                else:
                    state.par = re.sub(r"^\s*\\noindent(\s+|([^a-zA-Z\s])|$)", r"\2", state.par)

            # -----------------------------------------------------------------
            # String replacement (e.g., Greek letters, symbols)
            # -----------------------------------------------------------------
            elif typ == "string":
                content = state.contents.get(pure, "")
                # Avoid double spacing: if content starts with space and
                # the last output ends with space, strip the leading space
                if content.startswith(" ") and state.out:
                    last_parts = state.out[-1].split(",", 4)
                    last_s = last_parts[4] if len(last_parts) > 4 else ""
                    if last_s.endswith(" "):
                        content = content[1:]
                stack.puts(content, True)  # no_expand=True to preserve spacing

            # -----------------------------------------------------------------
            # Commands to ignore completely
            # -----------------------------------------------------------------
            elif typ == "nothing":
                pass

            # -----------------------------------------------------------------
            # Unknown command - output as-is
            # -----------------------------------------------------------------
            else:
                stack.puts(piece)

        # Update token pattern based on current mode
        token_re = re.compile(tokenpattern if state.tokenByToken[-1] else multitokenpattern)

    # Flush any remaining output
    if state.out:
        stack.finishBuffer()
    return True
