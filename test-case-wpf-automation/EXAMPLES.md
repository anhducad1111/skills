# Examples: WPF UI Automation Patterns

## Example 1: Configure and launch harness

```python
# utils.py — top of file (only these 3 lines are project-specific)
APP_PATH        = r"C:\MyProject\bin\Debug\MyApp.exe"
WINDOW_TITLE_RE = r".*MyApp.*"
DEFAULT_PORT    = "COM3"

# test_module.py
from utils import AppTester, log_test, log_info

class MyTester(AppTester):
    pass

t = MyTester()
t.launch()
```

---

## Example 2: Connect flow + error dialog handling

```python
def test_wrong_port(tester):
    """Expect error dialog when connecting to a non-responding port."""
    tester._find_by_id("PortSelector", "ComboBox").select("COM99")
    tester._invoke(tester._find_by_id("ConnectBtn", "Button"))

    # check_for_error_dialog handles embedded, top-level, and Win32 dialogs
    msg = tester.check_for_error_dialog(timeout=15)
    if msg:
        log_test("TC-001", "PASS", f"Dialog caught: {msg}")
        return True
    log_test("TC-001", "FAIL", "No error dialog appeared")
    return False


def test_successful_connect(tester, port="COM3"):
    """Connect to valid port and verify UI shows connected state."""
    result = tester.ensure_connected(port)
    if result:
        log_test("TC-002", "PASS", f"Connected on {port}")
    else:
        log_test("TC-002", "FAIL", "Connection did not succeed")
    return result
```

---

## Example 3: Text field injection via ValuePattern

```python
def test_valid_settings(tester):
    """Inject settings and verify action button becomes enabled."""
    # _set_text uses set_edit_text() — no keyboard simulation
    tester._set_text(tester._find_by_id("GainInput", "Edit"), "3.14")
    tester._set_text(tester._find_by_id("OffsetInput", "Edit"), "0.01")
    time.sleep(0.5)  # allow On<Prop>Changed + NotifyCanExecuteChanged to fire

    btn = tester._find_by_id("ApplySettingsBtn", "Button")
    if not btn.is_enabled():
        log_test("TC-010", "FAIL", "Apply button not enabled after valid inputs")
        return False

    tester._invoke(btn)
    log_test("TC-010", "PASS", "Settings applied")
    return True
```

---

## Example 4: Masked PIN / secret input (PasswordBox replacement)

```python
# WPF side: TextBox with Foreground=Transparent + bullet overlay template
# UIA side: value is fully readable via ValuePattern

CORRECT_PIN = "1234"
WRONG_PIN   = "9999"

def enter_pin(tester, pin: str):
    """Enter digit-by-digit into masked TextBox fields (PinInputBox1..4)."""
    for i, digit in enumerate(pin[:4], 1):
        tester._set_text(tester._find_by_id(f"PinInputBox{i}", "Edit"), digit)
        time.sleep(0.1)
    tester._invoke(tester._find_by_id("PinSubmitBtn", "Button"))
    time.sleep(0.5)

def read_pin_status(tester) -> str:
    """
    Status TextBlock is ALWAYS in UIA tree (only inner element hides, not container).
    Returns empty string when no message is set.
    """
    return tester._read_text("PinStatusText") or ""

def test_wrong_pin(tester):
    enter_pin(tester, WRONG_PIN)
    status = read_pin_status(tester)
    if status and ("incorrect" in status.lower() or "invalid" in status.lower()):
        log_test("TC-020", "PASS", f"Rejected: '{status}'")
        return True
    log_test("TC-020", "FAIL", f"No rejection message (got: '{status}')")
    return False
```

---

## Example 5: Multi-step wizard flow

```python
def test_wizard_nominal(tester):
    """Walk through a 3-step collection wizard and apply result."""
    # Navigate
    tester._invoke(tester._find_by_id("NavFeatureBtn", "Button"))
    time.sleep(0.4)

    # Collect 3 data points
    for i in range(1, 4):
        btn_id = f"CollectPoint{i}Btn"
        if not tester._wait_enabled(btn_id, timeout=10):
            log_test("TC-030", "FAIL", f"{btn_id} never became enabled")
            return False
        tester._invoke(tester._find_by_id(btn_id, "Button"))
        log_info(f"Collected point {i}/3")
        time.sleep(0.5)

    # Advance to preview screen
    tester._invoke(tester._find_by_id("WizardNextBtn", "Button"))
    time.sleep(0.5)

    # Apply — button must be enabled now
    apply_btn = tester._find_by_id("FeatureApplyBtn", "Button")
    if not apply_btn.is_enabled():
        log_test("TC-030", "FAIL", "Apply button not enabled on preview screen")
        return False

    tester._invoke(apply_btn)
    log_test("TC-030", "PASS", "Wizard completed and applied")
    return True
```

---

## Example 6: Read calibration/feature status (always navigate to status tab first)

```python
def test_feature_status(tester):
    """
    Verify a feature shows 'Configured' status.
    IMPORTANT: Always click the Status tab button before reading status,
    because the app may have been left on a different sub-tab by a prior test.
    """
    tester._invoke(tester._find_by_id("NavFeatureBtn", "Button"))
    time.sleep(0.4)
    tester._invoke(tester._find_by_id("FeatureStatusTabBtn", "Button"))
    time.sleep(0.4)

    texts = tester.main_win.descendants(control_type="Text")
    for t in texts:
        if "Configured" in t.window_text():
            log_test("TC-040", "PASS", "Status shows 'Configured'")
            return True

    log_test("TC-040", "FAIL", "Status 'Configured' not found")
    return False
```

---

## Example 7: Fault/error state guardrails

```python
def inject_fault_state(tester):
    """Trigger a fault condition via a known sentinel value (app/FW specific)."""
    tester._set_text(tester._find_by_id("InputField", "Edit"), "FAULT_SENTINEL_VALUE")
    tester._invoke(tester._find_by_id("SubmitBtn", "Button"))
    time.sleep(8)  # wait for device/app to enter fault state

def test_input_disabled_during_fault(tester):
    """During a fault state, primary inputs must be locked."""
    field = tester._find_by_id("InputField", "Edit")
    if not field.is_enabled():
        log_test("TC-050", "PASS", "Input disabled during fault state")
        return True
    log_test("TC-050", "FAIL", "Input still enabled during fault state")
    return False

def test_action_disabled_during_fault(tester):
    """Action buttons must be disabled when device is in fault state."""
    btn = tester._find_by_id("SubmitBtn", "Button")
    if not btn.is_enabled():
        log_test("TC-051", "PASS", "Action button disabled during fault")
        return True
    log_test("TC-051", "FAIL", "Action button enabled during fault")
    return False
```

---

## Example 8: Check TC coverage

```powershell
# From your test-app directory:
python case_cover.py

# With extra info on implemented-but-not-specced TCs:
python case_cover.py --verbose
```

Output:
```
==================================================
Test Case Coverage Report
==================================================
Spec TCs:        42
Implemented TCs: 38
Coverage:        35/42

[MISSING] 7 TCs in specs but NOT in scripts:
  - TC-015
  - TC-023
  ...
```

---

## Example 9: AutomationId quick-reference naming

```
# Pattern: <Feature><Role><Type>

# Dialogs
ConnectionErrorDialog           # overlay Grid root
ConnectionErrorDialogMessage    # inner TextBlock
ConnectionErrorDialogOkBtn      # dismiss button

# Navigation
NavDashboardBtn
NavSettingsBtn

# Wizard
FeatureWizardRoot
FeatureStatusTabBtn             # summary/overview tab
FeatureCollectTabBtn            # data collection tab
WizardNextBtn
WizardCancelBtn
WizardCancelDialog
WizardCancelDialogYesBtn
WizardCancelDialogNoBtn

# Inputs and validation
GainInput                       # TextBox for value entry
GainValidationErrorText         # TextBlock, hidden until GainValid=False

# Masked PIN (PasswordBox replacement)
PinInputBox1 .. PinInputBox4    # ValuePattern-writable masked TextBoxes
PinSubmitBtn
PinStatusText                   # ALWAYS in tree (container is never hidden)

# Actions
ApplySettingsBtn
ResetToDefaultBtn
CollectPoint1Btn .. CollectPoint3Btn
```
