"""
Package entry point for running tex2utf as a module.

This file enables the package to be executed with:
    python -m refactor input.tex

It simply delegates to the main() function in refactor.py.
"""

from .refactor import main

if __name__ == "__main__":
    main()
