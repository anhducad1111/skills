# Chart UI Structure

Good chart performance starts with good layout decisions.

## 1) Recommended composition

- toolbar row (window controls, zoom, mode toggles)
- chart canvas area
- optional horizontal scrollbar below chart
- side legend panel outside chart draw surface

This keeps plot rendering focused and avoids clutter in draw area.

## 2) Control responsibilities

### Toolbar
- command triggers only
- no heavy compute in click handlers

### Chart view
- interaction handlers (wheel/double-click/drag)
- render timer and refresh orchestration

### ViewModel
- state flags (`AutoFollow`, `AutoScaleY`, `Freeze`)
- command routing
- worker setup/lifecycle

## 3) Binding principles

- bind stable state, not high-frequency raw points
- use `INotifyPropertyChanged` for low-rate properties
- avoid flooding bindings with per-sample updates

## 4) Legend strategy

For many channels, prefer custom legend panel:
- supports virtualization/styling
- decouples legend complexity from plot drawing

Avoid frequent toggling of built-in heavy legend if not needed.

## 5) Scrollbar placement and behavior

- place directly under chart for discoverability
- hide when full range is visible
- show with proportional thumb when zoomed

## 6) Multi-view consistency

If app has both live and history chart:
- keep gesture semantics identical where possible
- share interaction helper utilities
- keep separate controllers for independent state

## 7) UI anti-patterns

- embedding complex templated controls on top of plot surface
- overly frequent style or visual tree changes during streaming
- repeated DataContext churn that restarts chart state unexpectedly
