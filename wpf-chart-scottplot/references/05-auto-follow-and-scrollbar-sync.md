# Auto Follow and Scrollbar Sync

This is often the hardest part of real-time chart UX.

## 1) Define two explicit navigation modes

### Auto-follow mode
- viewport tracks latest data
- window start = `max(0, total - visible)`
- scrollbar pinned near right edge

### Manual mode
- viewport start controlled by user
- auto-follow remains off until recenter action

Do not blend these modes implicitly.

## 2) Single source of truth for window start

Create a navigation controller that owns mutable window start index.
UI and worker read/write through this controller or well-defined setters.

Avoid independent duplicated states in multiple components.

## 3) Scrollbar synchronization model

On each render/update:
- compute max start
- clamp controller index
- update scrollbar min/max/value/step/thumb

On drag event:
- map scrollbar value back to start index
- disable follow mode

## 4) Re-entrancy protection

Use two flags:

- updating-from-code
- updating-from-user

If one flag is set, ignore the opposite callback path.
This prevents feedback loops and jitter.

## 5) Thumb sizing

Preferred method:
- use duration ratio if timestamps are available

Fallback:
- use visible/total point ratio

Thumb should clearly communicate zoom level.

## 6) Jump helpers

Provide explicit methods:
- `JumpToEnd(total, visible)`
- `ResetPosition()`
- `Pan(direction, visible, total)`
- `Clamp(total, visible)`

This keeps navigation logic reusable and testable.

## 7) UX details that matter

- pan step scales with visible window
- manual mode should persist through new incoming data
- follow mode should recover with one clear action (button/double-click)

## 8) Typical bugs

- scrollbar appears when no scrolling is possible
- thumb size not updating after zoom
- auto-follow silently re-enables during manual scroll
- off-by-one clamping at right edge
