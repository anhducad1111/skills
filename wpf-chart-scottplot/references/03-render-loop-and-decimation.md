# Render Loop and Decimation

This file covers how to keep ScottPlot fast with dense multi-channel data.

## 1) Render loop contract

Render loop should be deterministic:

1. guard (null, empty, hidden, frozen)
2. snapshot read
3. visible-range calculation
4. decimation factor selection
5. write reusable render buffers
6. update plottable metadata
7. update axes if required
8. refresh once

Avoid extra work outside this sequence.

## 2) Timer configuration

Use `DispatcherTimer` with explicit FPS target.

```csharp
_timer = new DispatcherTimer(DispatcherPriority.Input)
{
    Interval = TimeSpan.FromMilliseconds(1000.0 / 30.0)
};
_timer.Tick += (_, _) => RefreshPlot();
```

`Input` priority usually gives better interaction balance than `Render` for heavy charts.

## 3) Plottable reuse strategy

- create `Signal` plottables once
- keep `double[]` buffers alive
- update only `XOffset`, `Period`, render indices

Do not call plot clear/add on each frame.

## 4) Decimation as first-class logic

Render cost depends on points sent to GPU/CPU raster path.
Decimation should be explicit and tunable.

### Pixel-budget formula

```text
targetPoints = clamp(plotWidth * pointsPerPixel, minPts, maxPts)
decimationFactor = max(1, actualVisiblePoints / targetPoints)
```

### Why pixel-based

- stable appearance across window sizes
- stable frame cost across zoom levels
- avoids over-rendering invisible detail

## 5) Y-range strategy

In auto-scale mode:
- compute min/max during decimated buffer fill
- apply small padding

In manual mode:
- preserve user-selected Y limits
- only initialize once when switching out of auto mode

## 6) Axis update minimization

Axis setters can trigger expensive invalidation.
Cache last applied limits and skip no-op updates.

```csharp
if (Math.Abs(newYMin - _lastYMin) > epsilon ||
    Math.Abs(newYMax - _lastYMax) > epsilon)
{
    plot.Axes.SetLimitsY(newYMin, newYMax);
}
```

Use small epsilon to avoid floating-point jitter updates.

## 7) Re-entrancy guard

Prevent overlapping `RefreshPlot` runs.

```csharp
if (_isRefreshing) { _refreshPending = true; return; }
```

After completion, process one pending refresh if flagged.

## 8) No-visible-series edge case

If all channels hidden:
- set render indices to empty
- keep navigation and snapshot state coherent
- still refresh once so UI updates are visible

## 9) Optional debug instrumentation

Track per-frame timings:
- buffer fill ms
- layout/axis ms
- refresh ms

This helps separate algorithm bottlenecks from rendering bottlenecks.

## 10) Render anti-patterns

- allocating new arrays inside frame loop
- string formatting in hot path
- repeated legend rebuilds inside plot area
- full autoscale and full axis reset every frame
