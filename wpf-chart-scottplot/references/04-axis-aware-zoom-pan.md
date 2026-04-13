# Axis-Aware Zoom and Pan

High-quality chart UX requires predictable input semantics.

## 1) Hit-test regions

Use rendered data rectangle to classify wheel events:

- X-axis strip -> X zoom
- Y-axis strip -> Y zoom
- plot body with modifier (Ctrl) -> pan

This avoids accidental axis changes and improves precision.

## 2) Cursor-anchored Y zoom math

Given current Y range `[minY, maxY]` and cursor position ratio `p` from top:

```text
cursorY = maxY - p * (maxY - minY)
newRange = oldRange / zoomFactor
newMin = cursorY - (1 - p) * newRange
newMax = cursorY + p * newRange
```

This keeps the data under cursor visually anchored.

## 3) X zoom policy for streaming charts

Prefer changing logical window duration over arbitrary axis limits.
Reason:
- keeps worker-computed timeline and navigation coherent
- simplifies follow/manual mode behavior

## 4) Pan strategy

Pan step should scale with zoom:

```text
step = max(1, visibleCount * panRatio)
```

Typical `panRatio`: `0.05-0.10`.

## 5) Mode transitions

When user pans or manually drags scrollbar:
- disable auto-follow

When user resets/recenters/double-clicks:
- enable auto-follow
- optionally clear freeze and manual Y state

Make these transitions explicit and visible.

## 6) Input consistency rules

- wheel delta direction must be consistent across axes
- same gestures should mean same actions in live and history views
- avoid hidden gesture overloads

## 7) Example handler skeleton

```csharp
switch (target)
{
    case AxisTarget.XAxis:
        ZoomX(zoomIn ? 0.8 : 1.25);
        break;
    case AxisTarget.YAxis:
        ZoomYAtCursor(zoomIn ? 1.25 : 0.8, cursorY);
        break;
    case AxisTarget.ChartArea when ctrlPressed:
        PanX(zoomIn ? -1 : 1);
        break;
}
```

## 8) Interaction anti-patterns

- forcing all wheel input to one axis
- center-anchored Y zoom only
- pan that ignores current zoom level
- changing follow mode implicitly without clear user action
