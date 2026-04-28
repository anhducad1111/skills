---
name: test-case-wpf-automation
description: >
  Project-agnostic blueprint for automating WPF application test cases with
  pywinauto (UIA backend). Covers stable AutomationId assignment, custom modal
  design to replace MessageBox, real-time field validation with disabled buttons,
  headless UIA-only interaction (no mouse/keyboard hijacking), lazy UI tree cache,
  multi-step wizard flows, and deterministic state recovery between test cases.
  Use this skill when: writing new test scripts, adding AutomationId coverage,
  replacing native modal patterns, debugging flaky UIA scripts, or setting up
  test suites for any WPF desktop application.
---

# WPF Test Case Automation

## Quick Start

1. **Copy** `scripts/utils.py` into your test project. Set `APP_PATH`, `WINDOW_TITLE_RE`, `DEFAULT_PORT`.
2. **Instrument** all testable controls with `AutomationProperties.AutomationId`.
3. **Replace** all `MessageBox.Show` with custom WPF overlay panels that have explicit IDs.
4. **Validate fields in real-time** (`On<Prop>Changed`) and disable action buttons via `CanExecute` — never in click handlers.
5. **Script** using `_invoke()` / `_set_text()` only — no `click_input()`, no `type_keys()`.

---

## WPF Design Rules (before writing test scripts)

### Rule 1 — Custom Overlay Modals (not MessageBox)

`MessageBox.Show` creates a Win32 dialog that is unreliable under UIA.

**Use a WPF Grid overlay inside the main window's visual tree instead:**

```xml
<Grid AutomationProperties.AutomationId="SomeErrorDialog"
      Visibility="{Binding ShowErrorDialog, Converter={StaticResource BoolToVis}}"
      Background="{StaticResource OverlayBackdropColor}" Panel.ZIndex="1000">
    <Border Width="380" CornerRadius="4" Padding="24"
            VerticalAlignment="Center" HorizontalAlignment="Center">
        <StackPanel>
            <TextBlock AutomationProperties.AutomationId="SomeErrorDialogMessage"
                       Text="{Binding ErrorMessage}" TextWrapping="Wrap"/>
            <Button AutomationProperties.AutomationId="SomeErrorDialogOkBtn"
                    Content="OK" Command="{Binding DismissErrorCommand}"/>
        </StackPanel>
    </Border>
</Grid>
```

Every dialog must expose:
- `<Feature>Dialog` — root container ID
- `<Feature>DialogMessage` — status text ID
- `<Feature>DialogOkBtn` / `<Feature>DialogYesBtn` / `<Feature>DialogNoBtn` — action IDs

> **Why:** Overlay panels are always in the main window's visual tree.
> `child_window(auto_id="...")` finds them reliably.
> Top-level `ShowDialog()` windows require separate multi-path detection logic.

---

### Rule 2 — Real-time Validation + Disabled Buttons

Never validate on button click. **Validate on every keystroke** via
`partial void On<Prop>Changed`. Disable buttons via `CanExecute`, not `IsEnabled` in XAML.

```csharp
// Validation fires on every keystroke
partial void OnValueChanged(double value) => ValidateInput();

private void ValidateInput()
{
    IsValueValid = Value >= 0.0 && Value <= 1000.0;
    ValidationMessage = IsValueValid ? "" : "Value must be 0–1000";
    OnPropertyChanged(nameof(IsValueValid));
    SubmitCommand.NotifyCanExecuteChanged();
}

// Button state is the single source of truth
private bool CanSubmit() => IsConnected && IsValueValid;

[RelayCommand(CanExecute = nameof(CanSubmit))]
private async Task Submit() { ... }
```

**Wire notifications on state-driving properties:**

```csharp
[ObservableProperty]
[NotifyCanExecuteChangedFor(nameof(SubmitCommand))]
[NotifyPropertyChangedFor(nameof(IsEditingEnabled))]
private bool _isConnected;

[ObservableProperty]
[NotifyCanExecuteChangedFor(nameof(SubmitCommand))]
[NotifyCanExecuteChangedFor(nameof(UpdateConfigCommand))]
[NotifyPropertyChangedFor(nameof(IsEditingEnabled))]
private AppState _currentState;
```

**Validation feedback in XAML (hidden until invalid):**

```xml
<TextBlock AutomationProperties.AutomationId="FieldValidationErrorText"
           Text="{Binding ValidationMessage}">
    <TextBlock.Style>
        <Style TargetType="TextBlock">
            <Setter Property="Visibility" Value="Collapsed"/>
            <Style.Triggers>
                <DataTrigger Binding="{Binding IsValueValid}" Value="False">
                    <Setter Property="Visibility" Value="Visible"/>
                </DataTrigger>
            </Style.Triggers>
        </Style>
    </TextBlock.Style>
</TextBlock>
```

---

### Rule 3 — AutomationId Naming Convention

Pattern: `<Feature><Role><Type>`

| Control | Example ID |
|---|---|
| Dialog root | `FeatureErrorDialog` |
| Dialog message | `FeatureErrorDialogMessage` |
| Dialog confirm | `FeatureErrorDialogOkBtn` |
| Sidebar navigation | `NavSectionBtn` |
| Text input | `FieldNameInput` |
| Action button | `UpdateSettingsBtn` |
| Validation text | `FieldNameValidationErrorText` |
| Status text | `FeatureStatusText` |
| Wizard root | `FeatureWizardRoot` |
| Wizard step tab | `FeatureStepTabBtn` |

Rules:
- IDs must be **stable** — treat rename as a breaking API change
- IDs must **not encode visual order or index** (use semantic names)
- IDs must be **unique** across the entire application window

---

### Rule 4 — PasswordBox → Masked TextBox

`PasswordBox` blocks `ValuePattern`. Use a `TextBox` with visual masking instead
so automation can inject and read values while users see bullets:

```xml
<TextBox AutomationProperties.AutomationId="PinInputBox1"
         Foreground="Transparent"
         SelectionBrush="Transparent"
         CaretBrush="Transparent">
    <TextBox.Template>
        <ControlTemplate TargetType="TextBox">
            <Grid>
                <!-- Real text in here — transparent to user, readable by UIA -->
                <ScrollViewer x:Name="PART_ContentHost" Panel.ZIndex="1"/>
                <!-- Bullet shown when a character is entered -->
                <TextBlock Text="●" FontSize="20"
                           HorizontalAlignment="Center" VerticalAlignment="Center"
                           Visibility="{TemplateBinding Text,
                               Converter={StaticResource NullToVis},
                               ConverterParameter=inverse}"
                           Panel.ZIndex="0"/>
            </Grid>
        </ControlTemplate>
    </TextBox.Template>
</TextBox>
```

User sees `●`. Automation reads the real value via `ValuePattern`. No security compromise.

---

### Rule 5 — Status Text Always in UIA Tree

When a status message (error/success) is shown/hidden via `Visibility`, do not put the
`Visibility` binding on the **outer Border/container**. Put it only on the **inner TextBlock**.

```xml
<!-- ✗ WRONG — if Border is hidden, UIA cannot discover DacPasswordStatusText at all -->
<Border Visibility="{Binding HasMessage, Converter={StaticResource BoolToVis}}">
    <TextBlock AutomationProperties.AutomationId="FeatureStatusText" Text="{Binding StatusMessage}"/>
</Border>

<!-- ✓ CORRECT — Border always exists in tree; TextBlock hides when empty -->
<Border>
    <TextBlock AutomationProperties.AutomationId="FeatureStatusText"
               Text="{Binding StatusMessage}"
               Visibility="{Binding StatusMessage, Converter={StaticResource NullToVis},
                            ConverterParameter=inverse}"/>
</Border>
```

This ensures `child_window(auto_id="FeatureStatusText")` always resolves,
even before any message is shown.

---

## Python Script Rules

- Set `APP_PATH`, `WINDOW_TITLE_RE`, `DEFAULT_PORT` at top of `utils.py`.
- Use `AppTester.launch()` — never double-launch.
- Use `_find_by_id()` — lazy cache, re-traverses only on miss.
- Use `_invoke()` / `_set_text()` — never `click_input()` / `type_keys()`.
- Log every step with `log_test()` / `log_info()` (timestamped).
- Recover to known state before each test case.

---

## Scripts (in `scripts/`)

| File | Purpose |
|---|---|
| `utils.py` | Base `AppTester` class — copy and configure per project |
| `debug_tree.py` | Dump full UI tree to file when a control is missing |
| `case_cover.py` | Check TC coverage: spec Markdown vs. implemented scripts |

---

## Validation Checklist

- [ ] Every interactive control has a unique, stable `AutomationId`
- [ ] No `MessageBox.Show` in automated workflows — use overlay WPF dialogs
- [ ] All text inputs validate in real-time via `On<Prop>Changed`
- [ ] All action buttons use `CanExecute` — not hardcoded `IsEnabled` in XAML
- [ ] `IsConnected` / state properties have `NotifyCanExecuteChangedFor` on all dependent commands
- [ ] Panel-level `IsEnabled` computed props have `NotifyPropertyChangedFor` on source props
- [ ] Status/error TextBlocks are **always in UIA tree** (hide only inner element, not container)
- [ ] No `click_input()` / `type_keys()` in scripts — `ValuePattern` / `InvokePattern` only
- [ ] Each test leaves the app in a known ready state for the next test

---

## Detailed Reference

- Implementation patterns: [REFERENCE.md](REFERENCE.md)
- Runnable examples: [EXAMPLES.md](EXAMPLES.md)
- Ready-to-use scripts: [scripts/](scripts/)
