#!/usr/bin/env python3
"""Verify refactored version produces identical output to original."""

import subprocess
import sys
from pathlib import Path


def run_command(cmd):
    """Run a command and return its output."""
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    return result.stdout, result.stderr, result.returncode


def test_file(tex_file):
    """Test a single .tex file with both versions."""
    print(f"Testing: {tex_file.name}", end=" ... ")
    
    # Run original
    orig_cmd = [sys.executable, "tex2utf.py", str(tex_file)]
    orig_out, orig_err, orig_code = run_command(orig_cmd)
    
    # Run refactored
    refactor_cmd = [sys.executable, "refactor/refactor.py", str(tex_file)]
    ref_out, ref_err, ref_code = run_command(refactor_cmd)
    
    if orig_code != 0:
        print(f"SKIP (original failed: {orig_err.strip()})")
        return None
    
    if ref_code != 0:
        print(f"FAIL (refactor error: {ref_err.strip()})")
        return False
    
    if orig_out == ref_out:
        print("PASS")
        return True
    else:
        print("FAIL (output differs)")
        print(f"    Original length: {len(orig_out)}, Refactored length: {len(ref_out)}")
        
        # Find first difference
        min_len = min(len(orig_out), len(ref_out))
        for i in range(min_len):
            if orig_out[i] != ref_out[i]:
                start = max(0, i - 30)
                end = min(min_len, i + 30)
                print(f"    First diff at position {i}:")
                print(f"    Original: {repr(orig_out[start:end])}")
                print(f"    Refactor: {repr(ref_out[start:end])}")
                break
        else:
            if len(orig_out) != len(ref_out):
                print(f"    Outputs differ in length only")
        
        return False


def main():
    """Run tests on all .tex files in test directory."""
    test_dir = Path("test")
    
    if not test_dir.exists():
        print(f"Error: test directory not found at {test_dir.absolute()}")
        return 1
    
    tex_files = sorted(test_dir.glob("*.tex"))
    
    if not tex_files:
        print("No .tex files found in test directory")
        return 1
    
    print(f"Found {len(tex_files)} test files\n")
    
    passed = 0
    failed = 0
    skipped = 0
    
    for tex_file in tex_files:
        result = test_file(tex_file)
        if result is True:
            passed += 1
        elif result is False:
            failed += 1
        else:
            skipped += 1
    
    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed, {skipped} skipped")
    print(f"{'='*50}")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
