# Reference: WPF Automation Setup

## 1. AutomationId Coverage Matrix

### 1.1 Recommended ID groups (adapt naming to your project)

| Group | Example IDs |
|---|---|
| **App shell** | `MainWindowRoot`, section container roots |
| **Connection** | `PortSelector`, `BaudSelector`, `ConnectBtn` |
| **Error dialogs** | `ConnectionErrorDialog`, `ConnectionErrorDialogMessage`, `ConnectionErrorDialogOkBtn` |
| **Inputs** | `FieldNameInput` (one per field) |
| **Validation** | `FieldNameValidationErrorText` (hidden until invalid) |
| **Actions** | `SubmitBtn`, `UpdateSettingsBtn`, `ResetBtn` |
| **Navigation** | `NavSectionABtn`, `NavSectionBBtn` |
| **Wizards** | `FeatureWizardRoot`, `WizardStepTabBtn`, `WizardNextBtn`, `WizardCancelBtn` |
| **Cancel confirm** | `WizardCancelDialog`, `WizardCancelDialogYesBtn`, `WizardCancelDialogNoBtn` |
| **Status** | `FeatureStatusText` — **always in UIA tree** |

### 1.2 Naming rules
- IDs are a **public API** — rename = breaking change.
- Never encode visual index in ID (not `Button2`, `Row3`).
- One unique ID per control across the entire window.

---

## 2. Python Setup

### 2.1 Install
```powershell
python -m pip install pywinauto
```

### 2.2 Configure `utils.py`
```python
APP_PATH        = r"C:\path\to\YourApp.exe"
WINDOW_TITLE_RE = r".*YourApp.*"
DEFAULT_PORT    = "COM3"   # remove if project has no serial port
```

### 2.3 `AppTester` key methods

| Method | Behaviour |
|---|---|
| `launch()` | Attach to existing instance or start fresh. Never double-launches. |
| `_find_by_id(aid, ctrl_type)` | Lazy cached lookup. Re-traverses tree only on miss. |
| `_invoke(ctrl)` | InvokePattern → TogglePattern → SelectionItemPattern. Raises if disabled. |
| `_set_text(ctrl, value)` | `set_edit_text()` via ValuePattern. No keyboard simulation. |
| `_read_text(aid)` | Returns `window_text().strip()` or `None`. |
| `_toggle(ctrl, target)` | Set a CheckBox/ToggleButton to desired state. |
| `_wait_enabled(aid, timeout)` | Poll until control is enabled. |
| `ensure_connected(port)` | Select port + click Connect + wait for connected state. |
| `check_for_error_dialog()` | Detect + dismiss overlay / top-level / Win32 dialogs. |
| `dump_ui_tree(tag)` | Write full element tree to `ui_tree_<tag>_<ts>.log`. |

---

## 3. Dialog Detection Order

Always detect dialogs in this priority order:

```
1. Embedded overlay (in main window visual tree)
   → main_win.child_window(auto_id="FeatureDialog")
   → Most reliable — always present in UIA tree

2. Top-level UIA window (ShowDialog popup)
   → Desktop(backend="uia").window(auto_id="FeatureDialog", control_type="Window")

3. Process-scoped scan
   → Desktop(backend="uia").windows(process=pid)
   → Filter by title or child automation_id

4. Win32 ClassicMessageBox fallback (#32770)
   → Desktop(backend="uia").window(class_name="#32770", process=pid)
   → Last resort — only for legacy MessageBox.Show still in code
```

`check_for_error_dialog()` in `utils.py` implements all 4 paths automatically.

---

## 4. Real-time Validation — ViewModel Patterns

### 4.1 Notifying CanExecute when state changes

Any property that affects a button's availability must carry `NotifyCanExecuteChangedFor`:

```csharp
[ObservableProperty]
[NotifyCanExecuteChangedFor(nameof(SubmitCommand))]
[NotifyCanExecuteChangedFor(nameof(UpdateCommand))]
[NotifyPropertyChangedFor(nameof(IsEditingEnabled))]
private bool _isConnected;

[ObservableProperty]
[NotifyCanExecuteChangedFor(nameof(SubmitCommand))]
[NotifyPropertyChangedFor(nameof(IsEditingEnabled))]
private DeviceState _currentState;
```

### 4.2 Panel-level IsEnabled computed property

If a section's `IsEnabled` is bound to a computed property, that property must be notified:

```csharp
// XAML
<StackPanel IsEnabled="{Binding IsEditingEnabled}">

// ViewModel — must fire when any source changes
public bool IsEditingEnabled => IsConnected && !IsManualMode;

// Source props must carry NotifyPropertyChangedFor(nameof(IsEditingEnabled))
[ObservableProperty]
[NotifyPropertyChangedFor(nameof(IsEditingEnabled))]
private bool _isManualMode;
```

---

## 5. Wizard Flows

### 5.1 General wizard pattern
```python
# Navigate to feature
tester._invoke(tester._find_by_id("NavFeatureBtn", "Button"))
time.sleep(0.4)

# Go to specific wizard sub-tab
tester._invoke(tester._find_by_id("FeatureStepTabBtn", "Button"))
time.sleep(0.4)

# Wait for Next to become enabled (async operation may be running)
if not tester._wait_enabled("WizardNextBtn", timeout=10):
    raise RuntimeError("Wizard Next never became enabled")
tester._invoke(tester._find_by_id("WizardNextBtn", "Button"))
time.sleep(0.5)

# Apply result on preview screen
tester._invoke(tester._find_by_id("FeatureApplyBtn", "Button"))
```

### 5.2 Always navigate to Status/Summary tab before reading outcome
```python
# After any wizard flow that changes state, go to status tab first
tester._invoke(tester._find_by_id("NavFeatureBtn", "Button"))
time.sleep(0.4)
tester._invoke(tester._find_by_id("FeatureStatusTabBtn", "Button"))
time.sleep(0.4)
# Now safe to scan descendants for status text
```

---

## 6. Debugging Flaky Tests

### 6.1 Common failure causes

| Symptom | Cause | Fix |
|---|---|---|
| Button always disabled after connect | `NotifyCanExecuteChangedFor` missing on `IsConnected` | Add attribute to `_isConnected` field |
| Entire panel remains greyed out | `IsEnabled` computed prop not notified | Add `NotifyPropertyChangedFor(nameof(IsXxxEnabled))` to source props |
| Status text control not found | Container `Border` is hidden, not inner element | Move `Visibility` binding to inner TextBlock only |
| `_set_text` raises | `ValuePattern` not exposed | Ensure TextBox is not `IsReadOnly`, check binding mode |
| Dialog not detectable | Using `MessageBox.Show` | Replace with embedded WPF overlay dialog |
| Wrong status read in wizard | Landed on wrong sub-tab | Always click the Status/Summary tab button first |
| Test passes once then fails | Residual state from prior test | Add state reset / ensure_connected at start of each TC |

### 6.2 Run `debug_tree.py` to find missing IDs
```powershell
# With app running on the target screen:
python debug_tree.py
# Opens tree_debug.log — search for your control by text or class
```

### 6.3 Run `case_cover.py` to find unimplemented TCs
```powershell
python case_cover.py --verbose
```
