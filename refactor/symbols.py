"""
Symbol table initialization for tex2utf.

This module populates the symbol tables that define how LaTeX
commands are processed. It is called once at startup.

Symbol Tables Populated:
------------------------
- state.type_table: Maps command name -> handler type
- state.contents: Maps command name -> content or handler name
- state.environment: Maps environment name -> begin,end handlers
- state.environment_none: Set of environments to ignore

Handler Types:
--------------
- "string": Replace with fixed string (e.g., \\alpha -> α)
- "record": Replace with pre-built 2D record (e.g., \\sum)
- "sub": Call a function with no arguments
- "sub1", "sub2", "sub3": Collect 1/2/3 args, then call function
- "self": Output command name without backslash
- "trig": Trigonometric function (special argument handling)
- "fancy", "bold", "italic": Text style transformation
- "nothing": Ignore the command
- "discard1", "discard2": Consume and discard 1/2 arguments
- "def": User-defined macro (looked up in state.defs)

Categories of Symbols:
----------------------
1. Greek letters (\\alpha, \\beta, etc.)
2. Mathematical operators (\\cdot, \\times, etc.)
3. Relations (\\leq, \\geq, \\equiv, etc.)
4. Arrows (\\rightarrow, \\Leftarrow, etc.)
5. Big operators (\\sum, \\int, \\prod)
6. Delimiters (\\left, \\right, \\langle, etc.)
7. Accents (\\hat, \\tilde, \\bar, etc.)
8. Environments (matrix, align, equation, etc.)
"""

from . import state
from . import config
from .commands import define, defb


def init_symbols():
    """
    Initialize all symbol tables.

    This function must be called before processing any LaTeX input.
    It sets up all the built-in command definitions.
    """
    # =========================================================================
    # Big operators (multi-line records with limits above/below)
    # =========================================================================
    state.type_table["\\sum"] = "record"
    state.contents["\\sum"] = "3,3,1,0,__ \n❯  \n‾‾ "

    state.type_table["\\int"] = "record"
    state.contents["\\int"] = "3,2,1,0,╭ \n| \n╯ "

    state.type_table["\\oint"] = "record"
    state.contents["\\oint"] = "3,2,1,0,╭ \n⦶ \n╯ "

    state.type_table["\\prod"] = "record"
    state.contents["\\prod"] = "3,4,1,0,___ \n│ │ \n    "

    state.type_table["\\Sigma"] = "record"
    state.contents["\\Sigma"] = "3,2,1,0,__\n❯ \n‾‾"

    # =========================================================================
    # Greek letters
    # =========================================================================
    greek = {
        "\\alpha": "α", "\\beta": "β", "\\gamma": "γ", "\\delta": "δ",
        "\\epsilon": "ε", "\\zeta": "ζ", "\\eta": "η", "\\theta": "θ",
        "\\iota": "ι", "\\kappa": "κ", "\\lambda": "λ", "\\mu": "μ",
        "\\nu": "ν", "\\xi": "ξ", "\\pi": "π", "\\rho": "ρ",
        "\\sigma": "σ", "\\tau": "τ", "\\upsilon": "υ", "\\phi": "φ",
        "\\chi": "χ", "\\psi": "ψ", "\\omega": "ω", "\\Gamma": "Γ",
        "\\Delta": "△", "\\Theta": "Θ", "\\Lambda": "Λ", "\\Xi": "Ξ",
        "\\Pi": "π", "\\Upsilon": "Υ", "\\Phi": "Φ", "\\Psi": "Ψ",
        "\\Omega": "Ω",
    }
    for k, v in greek.items():
        state.type_table[k] = "string"
        state.contents[k] = v

    # =========================================================================
    # Mathematical symbols and operators
    # =========================================================================
    strings = {
        "\\,": " ",           # Thin space
        "\\;": " ",           # Thick space
        "\\|": "||",          # Double vertical bar
        "\\approx": " ≅ ",    # Approximately equal
        "\\backslash": "\\",  # Backslash
        "\\bullet": "•",      # Bullet operator
        "\\cap": " ∩ ",       # Intersection
        "\\cdot": " · ",      # Dot operator
        "\\cdots": "⋯",      # Centered dots
        "\\circ": " o ",      # Circle operator
        "\\colon": ": ",      # Colon
        "\\cong": "≅",        # Congruence
        "\\cup": " ∪ ",       # Union
        "\\dots": "...",      # Ellipsis
        "\\equiv": " ≡ ",     # Equivalent
        "\\exists": " ∃",     # Exists
        "\\forall": " ∀",     # For all
        "\\from": " <── ",    # From
        "\\ge": " ≥ ",        # Greater than or equal to
        "\\geq": " ≥ ",       # Greater than or equal to (alternative)
        "\\hbar": "ℏ",        # Reduced Planck's constant
        "\\hookleftarrow": " ↩ ", # Hooked left arrow
        "\\hookrightarrow": " ↪ ", # Hooked right arrow
        "\\in": " ∈ ",        # Element of
        "\\infty": "∞",      # Infinity
        "\\ldots": "...",      # Ellipsis (alternative)
        "\\Leftarrow": " <== ", # Left double arrow
        "\\leftarrow": " <── ", # Left arrow
        "\\leftrightarrow": " <──> ", # Left-right arrow
        "\\le": " ≤ ",        # Less than or equal to
        "\\leq": " ≤ ",       # Less than or equal to (alternative)
        "\\lhd": " ⊲ ",       # Left normal factor
        "\\longleftarrow": " <──── ", # Long left arrow
        "\\longleftrightarrow": " <────> ", # Long left-right arrow
        "\\longmapsto": " ├────> ", # Long mapsto
        "\\longrightarrow": " ────> ", # Long right arrow
        "\\ltimes": "⋉",      # Left semidirect product
        "\\mapsto": " ├──> ", # Mapsto
        "\\mid": " | ",       # Divides
        "\\mp": " ∓ ",        # Minus-plus
        "\\nabla": "∇",      # Nabla
        "\\ne": " ≠ ",        # Not equal
        "\\neg": "¬",        # Negate
        "\\neq": " ≠ ",       # Not equal (alternative)
        "\\ni": " ∌ ",        # Contains as member
        "\\nmid": " ∤ ",      # Does not divide
        "\\notin": " ∉ ",     # Not an element of
        "\\ominus": " ⊖ ",    # Circled minus
        "\\oplus": " ⊕ ",    # Circled plus
        "\\otimes": " ⊗ ",    # Circled times
        "\\owns": " ∋ ",      # Owns
        "\\partial": "∂",    # Partial derivative
        "\\pm": " ± ",        # Plus-minus
        "\\qed": "∎",        # End of proof
        "\\qquad": "     ",   # Large space
        "\\quad": "   ",      # Medium space
        "\\rhd": " ⊳ ",       # Right normal factor
        "\\Rightarrow": " ==> ", # Right double arrow
        "\\rightarrow": " ──> ", # Right arrow
        "\\rtimes": " ⋊ ",    # Right semidirect product
        "\\section": "Section ", # Section heading
        "\\setminus": " ⧹ ",  # Set minus
        "\\simeq": " ≃ ",     # Asymptotically equal
        "\\smallsetminus": " ⧵ ", # Small set minus
        "\\subsection": "Subsection ", # Subsection heading
        "\\subset": " ⊂ ",    # Subset
        "\\subseteq": " ⊆ ",  # Subset or equal
        "\\supset": " ⊃ ",    # Superset
        "\\supseteq": " ⊇ ",  # Superset or equal
        "\\textit": " ",      # Text in italics
        "\\times": " × ",     # Times
        "\\to": " ──> ",      # To
        "\\vee": " ∨ ",       # Logical OR
        "\\wedge": " ∧ ",     # Logical AND
        "~": " ",             # Tilde (space)
    }
    for k, v in strings.items():
        state.type_table[k] = "string"
        state.contents[k] = v

    # =========================================================================
    # Self-printing commands (output their name)
    # =========================================================================
    for cmd in [
        "@", "_", "$", "{", "}", "#", "&", "arg", "deg", "det",
        "dim", "gcd", "hom", "inf", "ker", "lim", "liminf",
        "limsup", "max", "min", "mod", "Pr", "sup", "%",
    ]:
        state.type_table[f"\\{cmd}"] = "self"

    # =========================================================================
    # Trigonometric functions (wrap argument in parentheses)
    # =========================================================================
    for cmd in [
        "arccos", "arcsin", "arctan", "cos", "cosh", "cot", "coth",
        "csc", "exp", "lg", "ln", "log", "sec", "sin", "sinh",
        "tan", "tanh",
    ]:
        state.type_table[f"\\{cmd}"] = "trig"

    # =========================================================================
    # Text style commands
    # =========================================================================
    for cmd in ["mathcal"]:
        state.type_table[f"\\{cmd}"] = "fancy"

    for cmd in ["mathbf"]:
        state.type_table[f"\\{cmd}"] = "bold"

    for cmd in ["mathit"]:
        state.type_table[f"\\{cmd}"] = "italic"

    for cmd in ["mathbb"]:
        state.type_table[f"\\{cmd}"] = "double"

    # =========================================================================
    # Commands to ignore completely
    # =========================================================================
    for cmd in [
        "text", "operatorname", "operatornamewithlimits", "relax",
        "-", "notag", "!", "/", "protect", "Bbb", "bf", "it", "em",
        "boldsymbol", "cal", "Cal", "goth", "ref", "maketitle",
        "expandafter", "csname", "endcsname", "makeatletter",
        "makeatother", "topmatter", "endtopmatter", "rm",
        "NoBlackBoxes", "document", "TagsOnRight", "bold", "dsize",
        "roster", "endroster", "endkey", "endRefs", "enddocument",
        "displaystyle", "twelverm", "tenrm", "twelvefm", "tenfm",
        "hbox", "mbox",
    ]:
        state.type_table[f"\\{cmd}"] = "nothing"

    # =========================================================================
    # Commands that trigger paragraph breaks
    # =========================================================================
    for cmd in [
        "par", "endtitle", "endauthor", "endaffil", "endaddress",
        "endemail", "endhead", "key", "medskip", "smallskip",
        "bigskip", "newpage", "vfill", "eject", "endgraph",
    ]:
        state.type_table[f"\\{cmd}"] = "sub"
        state.contents[f"\\{cmd}"] = "do_par"

    for cmd in ["proclaim", "demo"]:
        state.type_table[f"\\{cmd}"] = "par_self"

    for cmd in ["endproclaim", "enddemo"]:
        state.type_table[f"\\{cmd}"] = "self_par"

    # =========================================================================
    # Discarding commands (consume arguments but do nothing)
    # =========================================================================
    for cmd in [
        "bibliography", "myLabel", "theoremstyle", "theorembodyfont",
        "bibliographystyle", "hphantom", "vphantom", "phantom", "hspace",
    ]:
        state.type_table[f"\\{cmd}"] = "discard1"

    for cmd in ["numberwithin", "newtheorem", "renewcommand", "setcounter"]:
        state.type_table[f"\\{cmd}"] = "discard2"

    # =========================================================================
    # Special command handling
    # =========================================================================
    state.type_table["\\let"] = "sub"
    state.contents["\\let"] = "let_exp"
    state.type_table["\\def"] = "sub"
    state.contents["\\def"] = "def_exp"
    state.type_table["\\item"] = "sub"
    state.contents["\\item"] = "item"
    state.type_table["{"] = "sub"
    state.contents["{"] = "open_curly"
    state.type_table["}"] = "sub"
    state.contents["}"] = "close_curly"
    state.type_table["&"] = "sub"
    state.contents["&"] = "ampersand"
    state.type_table["$"] = "sub"
    state.contents["$"] = "dollar"
    state.type_table["$$"] = "sub"
    state.contents["$$"] = "ddollar"
    state.type_table["\\\\"] = "sub"
    state.contents["\\\\"] = "bbackslash"
    state.type_table["@"] = "sub"
    state.contents["@"] = "at"
    state.type_table["\\over"] = "sub"
    state.contents["\\over"] = "over"
    state.type_table["\\choose"] = "sub"
    state.contents["\\choose"] = "choose"
    state.type_table["\\noindent"] = "sub"
    state.contents["\\noindent"] = "noindent"
    state.type_table["\\left"] = "sub"
    state.contents["\\left"] = "left"
    state.type_table["\\right"] = "sub"
    state.contents["\\right"] = "right"

    # =========================================================================
    # Commands with special argument collection
    # =========================================================================
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
        state.type_table[k] = "sub1"
        state.contents[k] = v

    state.type_table["\\frac"] = "sub2"
    state.contents["\\frac"] = "fraction"

    # =========================================================================
    # Superscripts and subscripts
    # =========================================================================
    state.type_table["^"] = "sub1"
    state.contents["^"] = "superscript"
    state.type_table["_"] = "sub1"
    state.contents["_"] = "subscript"

    # =========================================================================
    # Buildrel command (for relations with limits)
    # =========================================================================
    state.type_table["\\buildrel"] = "sub3"
    state.contents["\\buildrel"] = "buildrel"

    # =========================================================================
    # Matrix environments (special handling for matrix-like structures)
    # =========================================================================
    state.type_table["\\matrix"] = "sub"
    state.contents["\\matrix"] = "do_matrix"

    for env in ["equation", "gather", "align"]:
        state.environment[env] = "ddollar,ddollar"

    for env in ["matrix", "CD", "smallmatrix"]:
        state.environment[env] = "matrix,endmatrix;1;c"

    # Environments to ignore
    for env in ["document", "split", "enumerate"]:
        state.environment_none[env] = True

    # =========================================================================
    # Detailed environment definitions
    # =========================================================================
    state.environment["Sb"] = "subscript:matrix,endmatrix;1;l"
    state.environment["Sp"] = "superscript:matrix,endmatrix;1;l"
    state.environment["eqnarray"] = "ddollar:matrix,endmatrix;0;r;c;l:ddollar"
    state.environment["split"] = "ddollar:matrix,endmatrix;0;r;l:ddollar"
    state.environment["multiline"] = "ddollar:matrix,endmatrix;0;r;l:ddollar"
    state.environment["align"] = "ddollar:matrix,endmatrix;0;r;l:ddollar"
    state.environment["aligned"] = "matrix,endmatrix;0;r;l"
    state.environment["gather"] = "ddollar:matrix,endmatrix;0;c:ddollar"
    state.environment["gathered"] = "matrix,endmatrix;0;c"
    state.environment["array"] = "arg2stack:matrix,endmatrixArg;1"
    state.environment["bmatrix"] = "beg_lr;[;]:matrix,endmatrix;1;c"
    state.environment["vmatrix"] = "beg_lr;|;|:matrix,endmatrix;1;c"

    if config.opt_TeX:
        define("\\pmatrix#1", "\\left(\\begin{matrix}#1\\end{matrix}\\right)")
    else:
        state.environment["pmatrix"] = "beg_lr;(;):matrix,endmatrix;1;c"

    # =========================================================================
    # Define big operator commands (e.g., \bigoplus)
    # =========================================================================
    for op in ["oplus", "otimes", "cup", "wedge"]:
        state.type_table[f"\\big{op}"] = state.type_table.get(f"\\{op}", "string")
        state.contents[f"\\big{op}"] = state.contents.get(f"\\{op}", "")

    # =========================================================================
    # Macro definitions (shortcuts and compatibility)
    # =========================================================================
    define("\\define", "\\def")
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
        "vmatrix", "Vmatrix", "smallmatrix", "bmatrix", "Sp", "Sb",
        "CD", "align", "aligned", "split", "multiline", "gather", "gathered",
    )

    # Clean up any trailing newlines in records
    for k in list(state.contents.keys()):
        if state.type_table.get(k) == "record" and state.contents[k].endswith("\n"):
            state.contents[k] = state.contents[k][:-1]
