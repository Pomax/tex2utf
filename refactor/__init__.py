"""
tex2utf refactored package.

This package is a modular refactoring of the original tex2utf.py script,
which converts LaTeX/TeX mathematical notation to UTF-8 plain text with
ASCII art representations of mathematical structures.

Module Structure:
-----------------
- config.py: Global configuration variables and debug logging
- state.py: Mutable global state shared across all modules
- records.py: Core data structure for 2D text layout (height, width, baseline)
- join.py: Horizontal joining of records (separate to avoid circular imports)
- brackets.py: Generation of tall bracket characters (parentheses, brackets, etc.)
- output.py: Final output formatting and printing
- stack.py: Group/scope management for nested LaTeX structures
- math_ops.py: Mathematical constructs (fractions, subscripts, superscripts, etc.)
- commands.py: LaTeX command handlers (\\frac, \\left, \\right, etc.)
- symbols.py: Symbol table initialization (Greek letters, operators, etc.)
- text_transforms.py: Unicode text style conversions (bold, italic, script)
- parser.py: Main tokenizer and paragraph processor
- refactor.py: Command-line entry point

Usage:
------
    python -m refactor input.tex
    python refactor/refactor.py input.tex
"""

from .refactor import main

__all__ = ['main']
