"""
utils.py — Generic WPF UI Automation harness for pywinauto (UIA backend).

Configuration:
    Set APP_PATH, WINDOW_TITLE_RE, and DEFAULT_PORT at the top of this file
    (or override in each test module) to adapt this harness to any WPF project.

Design principles:
    - No click_input() / type_keys()  →  UIA ValuePattern / InvokePattern only
    - Lazy window cache               →  only re-traverses tree on cache miss
    - Timestamped colored logging     →  every action is auditable
    - attach_or_launch()              →  never double-launches a running instance

Usage:
    from utils import AppTester, log_test, log_info
"""

import time
import sys
from datetime import datetime
from pywinauto import Application, Desktop, timings

timings.Timings.fast()  # Remove all WPF animation delays globally

# ─────────────────────────────────────────────────────────────────────────────
# Project-specific configuration — change these for each project
# ─────────────────────────────────────────────────────────────────────────────
APP_PATH        = r"C:\path\to\YourApp.exe"
WINDOW_TITLE_RE = r".*YourApp.*"
DEFAULT_PORT    = "COM3"
# ─────────────────────────────────────────────────────────────────────────────


# ── Logging ──────────────────────────────────────────────────────────────────

def log_test(name, status, msg=""):
    """Timestamped, colored test result log."""
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    colors = {
        "PASS":  "\033[92m",
        "FAIL":  "\033[91m",
        "SKIP":  "\033[93m",
        "INFO":  "\033[94m",
        "RESET": "\033[0m",
    }
    c = colors.get(status, colors["RESET"])
    print(f"[{ts}] {c}[{status}] {name}: {msg}{colors['RESET']}")

def log_info(msg):
    """Timestamped info log (no test ID)."""
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{ts}] \033[94m[INFO]\033[0m {msg}")


# ── Core Harness ──────────────────────────────────────────────────────────────

class AppTester:
    """
    Generic UIA test harness for WPF applications.

    Subclass this in each test module to add domain-specific helpers.
    All interactions go through _invoke() / _set_text() — never mouse/keyboard.
    """

    def __init__(self):
        self.app      = None
        self.main_win = None

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    def launch(self, timeout=30):
        """Attach to a running instance or start fresh. Never double-launches."""
        try:
            self.app = Application(backend="uia").connect(path=APP_PATH)
            log_info("Found existing instance. Attaching...")
        except Exception:
            log_info(f"Launching new App: {APP_PATH}")
            self.app = Application(backend="uia").start(APP_PATH)
            time.sleep(2)

        self._refresh_main_win(timeout=timeout)
        log_info("Application bound and ready.")

    def _refresh_main_win(self, timeout=10):
        try:
            if self.main_win and self.main_win.exists(timeout=0.1):
                return
            self.main_win = self.app.window(title_re=WINDOW_TITLE_RE, control_type="Window")
            self.main_win.wait("visible", timeout=timeout)
        except Exception:
            pass

    # ── Control lookup (lazy cache) ────────────────────────────────────────────

    def _find_by_id(self, aid, ctrl_type=None, timeout=2):
        """
        Find control by AutomationId.
        Fast path: checks cache first.
        Slow path: refreshes tree once on cache miss.
        """
        if not self.main_win:
            self._refresh_main_win()

        try:
            ctrl = self.main_win.child_window(auto_id=aid, control_type=ctrl_type)
            if ctrl.exists(timeout=0.1):
                return ctrl
        except Exception:
            pass

        # Cache miss — refresh and retry
        self._refresh_main_win()
        ctrl = self.main_win.child_window(auto_id=aid, control_type=ctrl_type)
        if not ctrl.exists(timeout=timeout):
            raise RuntimeError(f"Control not found: {aid!r} type={ctrl_type!r}")
        return ctrl

    # ── Interaction (UIA patterns only) ────────────────────────────────────────

    def _invoke(self, ctrl):
        """
        Trigger a control via InvokePattern → TogglePattern → SelectionItemPattern.
        Raises RuntimeError with a clear message if the control is disabled.
        No mouse interaction.
        """
        try:
            if not ctrl.is_enabled():
                raise RuntimeError("Target control is disabled")
        except RuntimeError:
            raise
        except Exception:
            pass

        for method in ("invoke", "toggle", "select"):
            try:
                getattr(ctrl, method)()
                return
            except Exception:
                continue

        raise RuntimeError(
            f"Unable to invoke control cleanly via UIA patterns. "
            f"Ensure {ctrl.element_info.control_type} supports Invoke, Toggle, or Selection."
        )

    def _toggle(self, ctrl, target_state=True):
        """Ensure a ToggleButton/CheckBox is in the desired state (True=On, False=Off)."""
        try:
            current = ctrl.get_toggle_state()  # 0=Off, 1=On
            if (current == 1) == target_state:
                return
        except Exception:
            pass
        self._invoke(ctrl)

    def _set_text(self, edit_ctrl, value):
        """
        Inject text into an Edit control via ValuePattern (set_edit_text).
        No keyboard simulation. Raises RuntimeError on failure.
        """
        try:
            edit_ctrl.set_edit_text(str(value))
        except Exception as e:
            raise RuntimeError(f"Unable to inject text cleanly via ValuePattern: {e}")

    def _read_text(self, aid, ctrl_type=None, timeout=1):
        """Read window_text() from a control by AutomationId. Returns None on failure."""
        try:
            ctrl = self._find_by_id(aid, ctrl_type, timeout=timeout)
            return ctrl.window_text().strip()
        except Exception:
            return None

    # ── Waits ──────────────────────────────────────────────────────────────────

    def _wait_enabled(self, aid, ctrl_type=None, timeout=8):
        """Poll until the control becomes enabled. Returns True/False."""
        end = time.time() + timeout
        while time.time() < end:
            try:
                c = self._find_by_id(aid, ctrl_type, timeout=0.1)
                if c.is_enabled():
                    return True
            except Exception:
                pass
            time.sleep(0.2)
        return False

    # ── Connection helpers ─────────────────────────────────────────────────────

    def _get_connect_btn(self):
        """Return the main Connect/Disconnect button control."""
        return self._find_by_id("ConnectBtn", "Button")

    def _is_connected_ui(self):
        """
        Detect connected state by reading the Connect button's child text.
        Assumes button shows "DISCONNECT" text when connected.
        """
        try:
            btn = self._get_connect_btn()
            texts = [t.window_text().upper() for t in btn.descendants(control_type="Text")]
            return "DISCONNECT" in texts
        except Exception:
            return False

    def ensure_connected(self, port=DEFAULT_PORT):
        """
        If not already connected, select port and click Connect.
        Returns True when UI shows connected state.
        """
        if self._is_connected_ui():
            return True

        log_info(f"Connecting to {port}...")
        try:
            self._find_by_id("PortSelector", "ComboBox").select(port)
            if not self._wait_enabled("ConnectBtn", timeout=5):
                log_test("CONNECT", "FAIL", "Connect button did not become actionable.")
                return False
            self._invoke(self._get_connect_btn())
        except Exception as e:
            log_test("CONNECT", "FAIL", f"Connection trigger failed: {e}")
            return False

        for _ in range(15):
            if self.check_for_error_dialog(timeout=0.5):
                return False
            if self._is_connected_ui():
                return True
            time.sleep(1)
        return False

    # ── Dialog detection and dismissal ────────────────────────────────────────

    def check_for_error_dialog(self, timeout=1):
        """
        Scan for embedded WPF overlay dialogs and native Win32 MessageBoxes.
        Dismisses by clicking the OK button automatically.

        Detection order:
          A. Embedded in main window visual tree (preferred — most reliable)
          B. Top-level UIA window dialog
          C. Win32 #32770 class fallback (handles legacy MessageBox.Show)

        Returns:
          str  — combined visible text of the dialog if found and dismissed
          None — if no dialog found within timeout
        """
        end_time = time.time() + timeout
        process_id = self.app.process if self.app else None

        while time.time() < end_time:
            for aid in ("ConnectionErrorDialog", "ValidationErrorDialog"):
                # A: Embedded overlay
                try:
                    dialog = self.main_win.child_window(auto_id=aid)
                    if dialog.exists(timeout=0.1):
                        msg = " ".join(
                            t.window_text()
                            for t in dialog.descendants(control_type="Text")
                            if t.window_text()
                        )
                        print(f"!!! Error Dialog Detected [embedded]: {msg}")
                        for btn_aid in (f"{aid}OkBtn", "OkBtn"):
                            try:
                                self._invoke(dialog.child_window(auto_id=btn_aid))
                            except Exception:
                                pass
                        if msg:
                            return msg
                except Exception:
                    pass

                # B: Top-level UIA window
                try:
                    dialog = Desktop(backend="uia").window(auto_id=aid, control_type="Window")
                    if dialog.exists(timeout=0.1):
                        msg = " ".join(
                            t.window_text()
                            for t in dialog.descendants(control_type="Text")
                            if t.window_text()
                        )
                        print(f"!!! Error Dialog Detected [top-level]: {msg}")
                        for btn_aid in (f"{aid}OkBtn", "OkBtn"):
                            try:
                                self._invoke(dialog.child_window(auto_id=btn_aid))
                            except Exception:
                                pass
                        if msg:
                            return msg
                except Exception:
                    pass

            # C: Win32 MessageBox fallback (class #32770)
            try:
                win32_dlg = Desktop(backend="uia").window(
                    class_name="#32770", process=process_id)
                if win32_dlg.exists(timeout=0.1):
                    msg = " ".join(
                        t.window_text()
                        for t in win32_dlg.descendants(control_type="Text")
                        if t.window_text()
                    ) or win32_dlg.window_text()
                    try:
                        self._invoke(win32_dlg.child_window(title="OK", control_type="Button"))
                    except Exception:
                        pass
                    return msg
            except Exception:
                pass

            time.sleep(0.2)
        return None

    # ── Debug helpers ──────────────────────────────────────────────────────────

    def dump_ui_tree(self, tag="fail"):
        """
        Dump the full UI element tree for the running application window.
        Output: ui_tree_<tag>_<timestamp>.log

        Call this when a control is mysteriously missing in automation.
        Caps at 200 descendants for speed.
        """
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ui_tree_{tag}_{ts}.log"
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"=== UI TREE DUMP [{tag}] ===\n")
                for win in Desktop(backend="uia").windows(process=self.app.process):
                    f.write(f"Window: {win.window_text()} "
                            f"[ID: {win.element_info.automation_id}]\n")
                    for child in win.descendants()[:200]:
                        f.write(
                            f"  - {child.element_info.control_type}: "
                            f"'{child.window_text()}' "
                            f"[ID: {child.element_info.automation_id}]\n"
                        )
            print(f"UI tree dumped to {filename}")
        except Exception as e:
            print(f"Failed to dump UI tree: {e}")
