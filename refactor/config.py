"""Configuration variables and constants for tex2utf.

This module contains all global configuration settings that control
the behavior of the LaTeX to UTF-8 converter. These values can be
modified at runtime via command-line arguments.

Configuration Variables:
------------------------
- linelength: Maximum line width for output (default: 150)
- maxdef: Maximum macro expansion depth to prevent infinite loops (default: 400)
- opt_by_par: Process input paragraph by paragraph
- opt_TeX: Use TeX compatibility mode
- opt_ragged: Use ragged right margin (no justification)
- opt_noindent: Suppress automatic paragraph indentation
- opt_debug: Enable debug logging to stderr

Token Patterns:
---------------
The module also defines regex patterns for tokenizing LaTeX input:
- usualtokenclass: Normal text characters
- notusualtokenclass: Special LaTeX characters (\\, $, {, }, etc.)
- macro: Pattern matching LaTeX macros (\\command)
- tokenpattern: Single token pattern
- multitokenpattern: Multiple consecutive tokens pattern
"""

# Configuration
linelength = 150
maxdef = 400
debug = 0
opt_by_par = False
opt_TeX = True
opt_ragged = False
opt_noindent = False
opt_debug = False

# Token patterns for LaTeX parsing
# Characters that are NOT regular text (special LaTeX characters)
notusualtokenclass = r"[\\${}^_~&@]"
# Characters that ARE regular text
usualtokenclass = r"[^\\${}^_~&@]"
# Pattern for LaTeX macros: backslash followed by either a single non-letter
# or a sequence of letters (with optional trailing whitespace)
macro = r"\\([^a-zA-Z]|([a-zA-Z]+\s*))"
# Active tokens: macros, $$, or special characters
active = f"{macro}|\\$\\$|{notusualtokenclass}"
# Pattern for a single token
tokenpattern = f"{usualtokenclass}|{active}"
# Pattern for multiple consecutive usual tokens or one active token
multitokenpattern = f"{usualtokenclass}+|{active}"


def debug_log(msg):
    """
    Log a debug message to stderr if debug mode is enabled.

    Args:
        msg: The message to log
    """
    if opt_debug:
        import sys
        print(f"DEBUG: {msg}", file=sys.stderr)
