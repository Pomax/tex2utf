#!/usr/bin/env python3
"""
tex2utf - Convert LaTeX/TeX to UTF-8 plain text with ASCII art.

This is the main entry point for the refactored tex2utf package.
It provides the same functionality as the original tex2utf.py but
with the code organized into separate modules.

Usage:
------
    python refactor/refactor.py input.tex
    python -m refactor input.tex

The program reads a LaTeX file and outputs a UTF-8 text representation
where mathematical formulas are rendered using Unicode characters and
ASCII art for structures like fractions, matrices, and radicals.

Example:
--------
Input:  $\\frac{a+b}{c}$
Output:
        a+b
        ───
         c

Command-line Arguments:
-----------------------
    filename      : Input TeX/LaTeX file
    --linelength  : Maximum output line width (default: 150)
    --ragged      : Use ragged right margin (no justification)
    --noindent    : Suppress automatic paragraph indentation
    --by_par      : Process input paragraph by paragraph
    --TeX         : Use TeX compatibility mode (default: True)
    --debug       : Enable debug output to stderr
"""

import sys
import os
import argparse

# Handle both package import and direct script execution
# When run as `python refactor/refactor.py`, __package__ is None
# When run as `python -m refactor`, __package__ is "refactor"
if __name__ == "__main__" and __package__ is None:
    # Running as script directly - add parent directory to path
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    __package__ = "refactor"

from . import config
from . import state
from . import stack
from .symbols import init_symbols
from .parser import paragraph


def main():
    """
    Main entry point for tex2utf.
    
    Parses command-line arguments, initializes the symbol tables,
    reads the input file, and processes it.
    """
    # Set up argument parser
    arg_parser = argparse.ArgumentParser(description="Convert TeX/LaTeX to UTF-8 text")
    arg_parser.add_argument("filename", help="Input TeX file")
    arg_parser.add_argument("--linelength", type=int, default=150,
                           help="Maximum line width for output")
    arg_parser.add_argument("--ragged", action="store_true",
                           help="Use ragged right margin (no justification)")
    arg_parser.add_argument("--noindent", action="store_true",
                           help="Suppress automatic paragraph indentation")
    arg_parser.add_argument("--by_par", action="store_true",
                           help="Process input paragraph by paragraph")
    arg_parser.add_argument("--TeX", action="store_true", default=True,
                           help="Use TeX compatibility mode")
    arg_parser.add_argument("--debug", action="store_true",
                           help="Enable debug output to stderr")
    args = arg_parser.parse_args()
    
    # Apply configuration from command-line arguments
    config.linelength = args.linelength
    config.opt_by_par = args.by_par
    config.opt_TeX = args.TeX
    config.opt_ragged = args.ragged
    config.opt_noindent = args.noindent
    config.opt_debug = args.debug
    
    # Initialize symbol tables (Greek letters, operators, environments, etc.)
    init_symbols()
    
    # Read input file
    try:
        with open(args.filename, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: File '{args.filename}' not found", file=sys.stderr)
        sys.exit(1)
    
    # Process the input
    if config.opt_by_par:
        # Process each paragraph separately (separated by blank lines)
        paragraphs = content.split("\n\n")
        for p in paragraphs:
            paragraph(p)
    else:
        # Process entire file at once
        paragraph(content)
    
    # Flush any remaining output
    stack.finishBuffer()


if __name__ == "__main__":
    main()
