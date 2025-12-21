"""
Global state management for tex2utf.

This module contains all mutable global state that is shared across
the various modules during LaTeX processing. The state tracks the
current parsing context, output buffers, and symbol tables.

Why Global State?
-----------------
The original tex2utf was a Perl script using global variables.
This design is preserved to maintain compatibility with the original
behavior. A future refactoring could encapsulate this state in a
class, but that would require significant changes to all modules.

State Categories:
-----------------

1. Parsing State:
   - level: Stack tracking nesting depth (indices into chunks)
   - chunks: Indices into 'out' marking logical group boundaries
   - tokenByToken: Stack of parsing mode flags
   - out: Main output buffer (list of records)
   - wait: Stack of expected closing tokens/events
   - action: Stack of callback names for when groups complete
   - curlength: Current line length for wrapping decisions
   - secondtime: Paragraph counter
   - argStack: Temporary storage for macro arguments
   - par: Current input being processed

2. Symbol Tables (populated by symbols.py):
   - type_table: Maps command name -> handler type
   - contents: Maps command name -> content/handler
   - args: Maps macro name -> argument count
   - defs: Maps macro name -> expansion text
   - environment: Maps environment name -> handlers
   - environment_none: Environments to ignore
"""

from typing import List, Dict, Any

# =============================================================================
# Parsing State - Tracks the current parsing context
# =============================================================================

# Stack of indices into 'chunks' array, tracking nesting levels.
# level[0] is always 0 (the base level).
# When we enter a group (e.g., { or $), we push a new level.
level: List[int] = [0]

# Indices into 'out' array marking where each logical chunk starts.
# A "chunk" is a unit of output that belongs together (like a single
# argument to a command, or content within braces).
chunks: List[int] = [0]

# Stack of parsing mode flags.
# 1 = parse one token at a time (for collecting macro arguments)
# 0 = can parse multiple usual characters at once (normal mode)
tokenByToken: List[int] = [0]

# Main output buffer: list of "record" strings.
# Each record represents a 2D text block with format:
#   "height,length,baseline,spaces,content"
out: List[str] = []

# Stack of expected closing delimiters or events.
# Examples: "}", "$", "$$", "endCell", "LeftRight", or an integer
# indicating how many chunks to collect before triggering action.
wait: List[Any] = [""]

# Stack of callback function names to invoke when groups complete.
# When wait[-1] is satisfied, action[-1] is called (via callsub).
action: List[str] = [""]

# Current accumulated line length in characters.
# Used to decide when to break lines.
curlength = 0

# Paragraph counter - incremented for each paragraph processed.
# Used to add blank lines between paragraphs after the first.
secondtime = 0

# Stack for temporarily storing macro arguments.
# Used by environments like {array} that take column specifiers.
argStack: List[str] = []

# Current input text being parsed.
# Modified as tokens are consumed and macros are expanded.
par = ""

# =============================================================================
# Symbol Tables - Define how LaTeX commands are processed
# =============================================================================

# Maps LaTeX command names (like "\\alpha" or "{") to handler types.
# Handler types include:
#   "string"  - Simple text replacement
#   "record"  - Pre-built 2D record (for \sum, \int, etc.)
#   "sub"     - Call a Python function
#   "sub1/2/3"- Collect 1/2/3 arguments, then call function
#   "def"     - User-defined macro (expand from defs table)
#   "self"    - Output command name without backslash
#   "trig"    - Trigonometric function (special handling)
#   "fancy"   - Script/calligraphic text style
#   "bold"    - Bold text style
#   "italic"  - Italic text style
#   "nothing" - Ignore completely
#   "discard1/2" - Consume and discard 1/2 arguments
type_table: Dict[str, str] = {}

# Maps LaTeX command names to their content or handler details.
# For "string" type: the replacement text (e.g., "α" for "\\alpha")
# For "record" type: the pre-built record string
# For "sub" types: the function name to call
contents: Dict[str, str] = {}

# Maps user-defined macro names to their argument counts.
# e.g., args["\\foo"] = 2 means \foo takes 2 arguments (#1 and #2)
args: Dict[str, int] = {}

# Maps user-defined macro names to their expansion text.
# e.g., defs["\\foo"] = "#1 + #2" expands \foo{a}{b} to "a + b"
defs: Dict[str, str] = {}

# Maps environment names to their begin/end handler specifications.
# Format: "begin_handlers,end_handlers"
# Handlers are colon-separated function names.
# Example: "ddollar:matrix,endmatrix;1;c" means:
#   - On \begin: call ddollar(), then matrix()
#   - On \end: call endmatrix("1;c")
environment: Dict[str, str] = {}

# Set of environment names that should be completely ignored.
# Processing continues inside these environments but \begin/\end
# are not output.
environment_none: Dict[str, bool] = {}


def reset_state():
    """
    Reset all global state to initial values.
    
    Useful for processing multiple documents or for testing.
    Does not reset symbol tables (type_table, contents, etc.)
    as those are typically set once at startup.
    """
    global level, chunks, tokenByToken, out, wait, action
    global curlength, secondtime, argStack, par
    
    level[:] = [0]
    chunks[:] = [0]
    tokenByToken[:] = [0]
    out[:] = []
    wait[:] = [""]
    action[:] = [""]
    curlength = 0
    secondtime = 0
    argStack[:] = []
    par = ""
