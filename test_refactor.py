#!/usr/bin/env python3
"""Test script to compare original tex2utf.py with refactored version."""

import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd):
    """Run a command and return its output."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout, result.stderr, result.returncode


def test_file(tex_file):
    """Test a single .tex file with both versions."""
    print(f"Testing: {tex_file}")
    
    # Run original
    orig_cmd = [sys.executable, "tex2utf.py", str(tex_file)]
    orig_out, orig_err, orig_code = run_command(orig_cmd)
    
    # Run refactored
    refactor_cmd = [sys.executable, "-m", "refactor", str(tex_file)]
    ref_out, ref_err, ref_code = run_command(refactor_cmd)
    
    if orig_out == ref_out:
        print(f"  ✓ PASS - Output matches")
        return True
    else:
        print(f"  ✗ FAIL - Output differs")
        print(f"  Original length: {len(orig_out)}")
        print(f"  Refactored length: {len(ref_out)}")
        # Show first difference
        for i, (c1, c2) in enumerate(zip(orig_out, ref_out)):
            if c1 != c2:
                print(f"  First diff at position {i}: orig={repr(c1)} ref={repr(c2)}")
                print(f"  Context orig: {repr(orig_out[max(0,i-20):i+20])}")
                print(f"  Context ref:  {repr(ref_out[max(0,i-20):i+20])}")
                break
        return False


def main():
    """Run tests on all .tex files in test directory."""
    test_dir = Path("test")
    if not test_dir.exists():
        print("No test directory found")
        return
    
    tex_files = list(test_dir.glob("*.tex"))
    if not tex_files:
        print("No .tex files found in test directory")
        return
    
    passed = 0
    failed = 0
    
    for tex_file in sorted(tex_files):
        if test_file(tex_file):
            passed += 1
        else:
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
