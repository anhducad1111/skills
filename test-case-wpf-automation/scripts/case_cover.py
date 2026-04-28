"""
case_cover.py — Test case coverage checker.

Compares TC IDs defined in test spec Markdown files with TC IDs
actually implemented in test script Python files.
Reports any TCs that appear in specs but have no automation coverage.

Configuration:
    Set SPEC_DIR and SCRIPTS_DIR to your project's paths.
    Adjust TC_PATTERN if your test IDs use a different format (e.g. "TST-\\d{4}").

Usage:
    python case_cover.py
    python case_cover.py --verbose
"""

import os
import re
import glob
import sys

# ─────────────────────────────────────────────────────────────────────────────
# Project-specific configuration
# ─────────────────────────────────────────────────────────────────────────────
SPEC_DIR       = r".\test-case"          # Directory containing .md spec files
SCRIPTS_DIR    = r"."                    # Directory containing test .py files
TC_PATTERN     = r"TC-\d{3}"            # Regex for test case IDs in both sources

# Files to exclude from script scanning (helpers, not test scripts)
EXCLUDE_FILES  = {"utils.py", "debug_tree.py", "debug_all.py", "case_cover.py"}
# ─────────────────────────────────────────────────────────────────────────────


def find_tc_ids(file_path, pattern=TC_PATTERN):
    """Extract all unique TC IDs from a file using regex."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return set(re.findall(pattern, content))
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return set()


def collect_spec_tcs():
    """Gather all TC IDs mentioned in Markdown spec files."""
    tcs = set()
    for f in glob.glob(os.path.join(SPEC_DIR, "**", "*.md"), recursive=True):
        tcs.update(find_tc_ids(f))
    return tcs


def collect_implemented_tcs():
    """Gather all TC IDs mentioned in Python test scripts."""
    tcs = set()
    for f in glob.glob(os.path.join(SCRIPTS_DIR, "*.py")):
        if os.path.basename(f) in EXCLUDE_FILES:
            continue
        tcs.update(find_tc_ids(f))
    return tcs


def run_coverage_check(verbose=False):
    spec_tcs        = collect_spec_tcs()
    implemented_tcs = collect_implemented_tcs()
    missing         = sorted(spec_tcs - implemented_tcs)
    extra           = sorted(implemented_tcs - spec_tcs)  # implemented but not in specs

    print("=" * 50)
    print("Test Case Coverage Report")
    print("=" * 50)
    print(f"Spec TCs:        {len(spec_tcs)}")
    print(f"Implemented TCs: {len(implemented_tcs)}")
    print(f"Coverage:        {len(implemented_tcs & spec_tcs)}/{len(spec_tcs)}")
    print()

    if missing:
        print(f"[MISSING] {len(missing)} TCs in specs but NOT in scripts:")
        for tc in missing:
            print(f"  - {tc}")
    else:
        print("[MISSING] None — full coverage!")

    if verbose and extra:
        print(f"\n[EXTRA] {len(extra)} TCs in scripts but NOT in specs (stubs/orphans):")
        for tc in extra:
            print(f"  + {tc}")

    return missing


if __name__ == "__main__":
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    run_coverage_check(verbose=verbose)
