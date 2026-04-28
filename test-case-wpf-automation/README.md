# test-case-wpf-automation

> **Reusable skill** for automating WPF desktop application test cases with `pywinauto` (UIA backend).
> Works with any WPF project — configure 3 lines and go.

---

## What this skill covers

| Area | What you get |
|---|---|
| **WPF design rules** | How to structure XAML/ViewModel so automation never breaks |
| **Custom modals** | Replace `MessageBox.Show` with testable WPF overlay dialogs |
| **Real-time validation** | Field validation on keystrokes + disabled buttons via `CanExecute` |
| **Masked PIN input** | `PasswordBox` → `TextBox` pattern that keeps `ValuePattern` writable |
| **Status text in UIA tree** | Why and how to keep status elements always discoverable |
| **Python harness** | `AppTester` base class — attach/launch, find, invoke, set text, dialog handling |
| **Wizard flows** | Navigate multi-step wizards deterministically |
| **Debug tooling** | UI tree dump + TC coverage checker |

---

## Files

```
test-case-wpf-automation/
├── SKILL.md        ← Rules, quick-start, WPF design checklist
├── REFERENCE.md    ← AutomationId matrix, API table, debug guide
├── EXAMPLES.md     ← 9 copy-paste patterns (connect, PIN, wizard, fault, coverage)
└── scripts/
    ├── utils.py        ← AppTester base class — configure 3 lines, use everywhere
    ├── debug_tree.py   ← Dump running app's UI element tree to file
    └── case_cover.py   ← Compare TC IDs in specs vs. scripts → find gaps
```

---

## Quick setup

### 1. Copy scripts into your test project

```
your-project/
└── test-app/
    ├── utils.py         ← from scripts/utils.py
    ├── debug_tree.py    ← from scripts/debug_tree.py
    ├── case_cover.py    ← from scripts/case_cover.py
    └── 01_connect.py   ← your test modules
```

### 2. Configure the 3 project-specific lines in `utils.py`

```python
APP_PATH        = r"C:\MyProject\bin\Debug\MyApp.exe"
WINDOW_TITLE_RE = r".*MyApp.*"
DEFAULT_PORT    = "COM3"          # remove if no serial port
```

### 3. Configure `case_cover.py`

```python
SPEC_DIR    = r".\test-case"     # where your .md spec files live
SCRIPTS_DIR = r"."               # where your test .py files live
TC_PATTERN  = r"TC-\d{3}"       # adjust if you use a different ID format
```

### 4. Install dependency

```powershell
python -m pip install pywinauto
```

---

## Usage patterns

### Run automation tests

```python
from utils import AppTester, log_test, log_info

class MyTester(AppTester):
    pass

t = MyTester()
t.launch()
t.ensure_connected()

# Find a control and invoke it
btn = t._find_by_id("SubmitBtn", "Button")
t._invoke(btn)

# Inject text (ValuePattern — no keyboard simulation)
t._set_text(t._find_by_id("GainInput", "Edit"), "3.14")

# Detect and dismiss error dialogs
msg = t.check_for_error_dialog(timeout=10)
```

### Dump UI tree (when a control is missing)

```powershell
# With your app open on the target screen:
python debug_tree.py
# → writes tree_debug.log
# Search by AutomationId, text, or control type to find your controls
```

### Check test coverage

```powershell
python case_cover.py
python case_cover.py --verbose   # also shows extra TCs not in specs
```

---

## Key WPF design rules (summary)

1. **Use WPF overlay Grid dialogs** — not `MessageBox.Show`
2. **Validate fields in `On<Prop>Changed`** — disable buttons via `CanExecute`, not XAML `IsEnabled`
3. **Name controls** as `<Feature><Role><Type>` (`SubmitBtn`, `GainValidationErrorText`)
4. **Replace `PasswordBox`** with a masked `TextBox` so `ValuePattern` works
5. **Never hide the status container** — only hide the inner `TextBlock` so the ID stays in UIA tree

See [SKILL.md](SKILL.md) for full rules, [EXAMPLES.md](EXAMPLES.md) for runnable patterns.

---

## Compatibility

- **WPF**: .NET 6+ (WPF on Windows)
- **Python**: 3.10+
- **pywinauto**: 0.6.8+
- **Backend**: `uia` only
