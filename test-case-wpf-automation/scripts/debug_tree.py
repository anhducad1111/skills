"""
debug_tree.py — Dump full WPF UI control tree to a log file.

Use this when automation cannot find a control:
  - Run while the app is open on the screen you want to inspect
  - Open tree_debug.log to search for AutomationId values

Configuration:
    Set APP_PATH and WINDOW_TITLE_RE to match your project (same as utils.py).

Usage:
    python debug_tree.py
    python debug_tree.py my_custom_output.log
"""

import sys
from pywinauto import Application, Desktop

# ─────────────────────────────────────────────────────────────────────────────
# Project-specific configuration — must match utils.py
# ─────────────────────────────────────────────────────────────────────────────
APP_PATH        = r"C:\path\to\YourApp.exe"
WINDOW_TITLE_RE = r".*YourApp.*"
# ─────────────────────────────────────────────────────────────────────────────


def dump_tree_to_file(filename="tree_debug.log"):
    """
    Connect to the running app and call print_control_identifiers().
    Output is redirected to 'filename' for offline analysis.
    """
    print(f"Dumping UI tree to {filename}...")
    app = Application(backend="uia").connect(path=APP_PATH)
    main_win = app.window(title_re=WINDOW_TITLE_RE)

    with open(filename, "w", encoding="utf-8") as f:
        old_stdout = sys.stdout
        sys.stdout = f
        try:
            main_win.print_control_identifiers()
        finally:
            sys.stdout = old_stdout

    print("Done.")


def dump_elements_inline(limit=100):
    """
    Quick inline dump: prints first <limit> descendants with type, ID, text.
    Useful for fast triage without opening a file.
    """
    desktop = Desktop(backend="uia")
    win = desktop.window(title_re=WINDOW_TITLE_RE, control_type="Window")
    if not win.exists(timeout=5):
        print("Window not found.")
        return

    print(f"Found Window: {win.window_text()}")
    print(f"Dumping first {limit} descendants:\n")

    for i, el in enumerate(win.descendants()[:limit]):
        try:
            aid  = el.element_info.automation_id
            txt  = el.window_text()
            tp   = el.element_info.control_type
            print(f"[{i:3}] {tp:20} | id='{aid}' | text='{txt}'")
        except Exception:
            pass


if __name__ == "__main__":
    output_file = sys.argv[1] if len(sys.argv) > 1 else "tree_debug.log"
    try:
        dump_tree_to_file(output_file)
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure the application is running!")
