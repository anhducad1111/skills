# ScottPlot Advanced Patterns

This reference focuses on ScottPlot-specific decisions for large-data WPF charts.
It complements architecture and performance docs, and helps with implementation tradeoffs.

## 1) Choosing the right plottable

ScottPlot offers multiple plottables. Picking the wrong one can cost an order of magnitude in performance.

### `Signal` (preferred for dense, evenly spaced data)

Use when:
- samples are evenly spaced in X
- you can represent X as `XOffset + index * Period`
- high point counts and frequent refresh are expected

Strengths:
- highly optimized for contiguous arrays
- minimal per-point overhead
- excellent for real-time waveforms and telemetry strips

Caveats:
- less flexible for irregular X spacing
- requires consistent mapping logic when decimating

### `Scatter` (for irregular X or sparse points)

Use when:
- each point has arbitrary X/Y
- you need non-uniform spacing or special marker behavior

Strengths:
- maximum flexibility

Caveats:
- generally heavier than `Signal` at high point counts
- markers and line complexity can become expensive quickly

### Rule of thumb

- For real-time multi-channel streams: start with `Signal`.
- Switch to `Scatter` only when your X semantics require it.

## 2) Pre-allocation and plottable lifetime

### Golden rule

Create plottables once, update metadata per frame.

Do:
- initialize plot and channel series at startup/reset
- reuse arrays
- update only changed properties in render loop

Do not:
- call `Clear()` and `Add.*` each frame
- recreate color/style objects in hot path

### Pattern

```csharp
// one-time init
Signal sig = plot.Add.Signal(channelBuffer);
sig.MaximumMarkerSize = 0;

// per-frame
sig.Data.XOffset = xOffset;
sig.Data.Period = period;
sig.MinRenderIndex = 0;
sig.MaxRenderIndex = lastIndex;
```

## 3) Decimation strategy with `Signal`

For dense windows, decimate before plotting.

### Index-step decimation

Most portable approach for streaming charts:

```text
decimationFactor = max(1, visiblePoints / targetPoints)
```

Then iterate by step and fill render buffer.

Benefits:
- deterministic cost
- simple math
- easy to tune

Tradeoff:
- may miss narrow spikes if factor is too large

### Min/Max envelope decimation (advanced)

For preserving peaks under heavy downsampling:
- for each bucket, compute min and max
- render both (sawtooth-like envelope)

Benefits:
- better peak preservation

Tradeoff:
- more CPU than simple step decimation
- more complex buffer management

Use envelope mode when peak integrity matters (fault detection, event spikes).

## 4) Axis management patterns

Axis operations are often more expensive than expected.

### Update only when changed

Cache last applied X/Y limits and compare with epsilon for Y.

```csharp
if (newXMin != lastXMin || newXMax != lastXMax)
    plot.Axes.SetLimitsX(newXMin, newXMax);

if (Math.Abs(newYMin - lastYMin) > epsilon ||
    Math.Abs(newYMax - lastYMax) > epsilon)
    plot.Axes.SetLimitsY(newYMin, newYMax);
```

### Auto-Y vs Manual-Y split

Auto-Y mode:
- compute min/max from currently rendered points
- add padding

Manual-Y mode:
- preserve user-selected range
- do not overwrite each frame

Switching between these modes should be explicit.

## 5) Tick generation and label formatting

Tick formatting can become a hidden hotspot.

### Best practice

- cache timeline and index context for formatter
- avoid expensive snapshot calls from inside formatter
- return empty string for out-of-range indices quickly

Formatter callbacks can fire frequently during interaction.
Keep logic lean and allocation-light.

### Time-axis labels for index-based data

When chart X is absolute sample index:
- convert index -> ring-buffer timestamp
- format with fixed pattern (e.g., `HH:mm:ss.ff`)

Do not perform heavy DateTime reconstruction in every callback if avoidable.

## 6) Styling for performance

Visual choices directly affect frame budget.

### Good defaults for live charts

- markers off (`MaximumMarkerSize = 0`)
- anti-aliasing off (or limited)
- moderate line width (`1.0-1.5`)
- legend off in plot (use external legend panel)

### Expensive features to use carefully

- dense marker rendering
- gradient fills and complex shadows
- frequent title/annotation text updates
- high-frequency axis relabeling with rich formatting

## 7) Input processor strategy

ScottPlot has built-in input handling, but custom handling is often better for controlled UX.

### Custom input path advantages

- exact axis-aware gesture semantics
- stable integration with follow/manual mode logic
- easier throttling and guard checks

### Built-in input path advantages

- faster to prototype
- less custom code

For high-performance production dashboards, custom input logic is usually worth it.

## 8) Refresh patterns and invalidation

`Refresh()` is the expensive boundary where draw work commits.

### Rules

- call once per render cycle
- avoid nested refresh triggers in helpers
- avoid refreshing from multiple unrelated events simultaneously

If helper methods must update axis state, prefer returning state changes to caller,
then let caller perform a single coordinated refresh.

## 9) Multi-channel scaling patterns

When channel count increases, use explicit visibility and loop optimizations.

### Visibility mask

Build bitmask of visible channels and skip hidden series early.

Benefits:
- fewer buffer writes
- less min/max work
- less plottable metadata churn

### Visible index cache

Collect visible channel indices into a compact array per frame,
then iterate only those indices in inner loops.

This avoids repeated branch checks in deepest loop.

## 10) Handling "no visible series"

If all channels are hidden:
- set render indices to empty
- keep navigation and axis state coherent
- still run minimal refresh to show empty state correctly

Without this path, toggling channels back on can leave stale state artifacts.

## 11) Live vs history plot profile

Use different profiles for live and history contexts.

### Live profile
- lower visual overhead
- strict frame-time budget
- aggressive guard checks

### History profile
- can allow richer interaction/detail
- may tolerate slightly higher render cost
- optional smoother anti-aliasing

Keep profile constants separate to avoid one-size-fits-none behavior.

## 12) Debug benchmark usage

Enable benchmark overlays in debug only.

Use benchmark output alongside app metrics:
- frame timing
- queue depth
- visible points
- decimation factor

A benchmark number alone is not enough without workload context.

## 13) Advanced decimation heuristics

Simple step decimation is usually enough, but advanced heuristics help in edge cases.

### Adaptive based on channel count

Increase decimation as number of visible channels rises:

```text
effectiveTarget = baseTarget / sqrt(max(1, visibleChannels / baselineChannels))
```

This keeps aggregate draw cost bounded at high channel counts.

### Adaptive based on frame-time feedback

Closed-loop approach:
- if frame time > budget for N consecutive frames, increase decimation
- if frame time well below budget for M frames, relax decimation slightly

Keep adjustments gradual to avoid visual oscillation.

## 14) Annotation and overlays

Overlays (markers, threshold lines, event annotations) are useful but can cost heavily.

Guidelines:
- pre-create reusable overlays when possible
- batch overlay updates
- avoid adding/removing many overlays every frame
- decouple overlay update rate from render rate if possible

## 15) Memory and GC tips specific to ScottPlot workflows

- reuse color objects where feasible
- avoid per-frame LINQ or temporary lists
- avoid per-frame string interpolation for titles/tooltips unless needed
- consider pooling large temporary arrays used in decimation

GC spikes often appear as periodic chart stutter; allocation discipline is critical.

## 16) Verification matrix for ScottPlot changes

When changing ScottPlot usage, test these scenarios:

1. max visible channels
2. rapid zoom in/out at various window widths
3. pan while stream is active
4. follow mode on/off transitions
5. channel visibility churn (all off/all on)
6. long run stability (30-60 min)

Track:
- FPS trend
- P95 frame time
- CPU trend
- managed allocations
- UI interaction latency

## 17) Troubleshooting quick map

Symptom -> likely ScottPlot-side cause:

- low FPS when zoomed out -> insufficient decimation or heavy axis/tick work
- lag spikes during interaction -> re-entrant refresh or costly tick formatter
- channel toggles feel expensive -> repeated plottable recreation or style churn
- jitter at steady load -> GC pressure from per-frame allocations

## 18) Portable template constants

Use this as a starting block in new projects:

```csharp
private const double TargetRenderFps = 30.0;
private const double PointsPerPixel = 0.9;
private const int MinDecimatedPoints = 180;
private const int MaxDecimatedPoints = 480;
private const double AxisEpsilon = 1e-5;
private const double PanRatio = 0.08;
```

Then tune per hardware/profile with measured data.

## 19) What not to do (ScottPlot edition)

- Do not recreate plot or plottables in render loop.
- Do not force full autoscale every frame in manual mode.
- Do not compute complex tick labels from expensive services each callback.
- Do not update title/legend text every frame unless required.
- Do not enable expensive visual effects by default in live views.

## 20) Decision summary

For most high-rate WPF charts:

1. choose `Signal`
2. use fixed ring buffers
3. decimate by pixel budget
4. cache axis/tick state
5. refresh once per frame
6. keep interaction logic explicit and mode-aware

These six decisions deliver most of the performance wins.
