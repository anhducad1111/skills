# Performance Guards

Guards are lightweight checks that prevent expensive no-value work.

## 1) Guard categories

### Visibility guards
- skip render when chart view/tab is not visible

### State guards
- skip render when no data or no channels visible

### Dirty guards
- skip frame when key state unchanged

### Axis guards
- skip axis setter calls when limits unchanged

### Freeze guards
- skip heavy refresh when in frozen mode and no interaction pending

## 2) Dirty-key design

Track these keys after each committed frame:
- total points
- window start
- visible count
- channel visibility mask
- oldest index (if ring wraps)

If all unchanged, return early.

## 3) Axis epsilon design

Use epsilon-based compare for floating values:

```text
if abs(new - old) <= epsilon then treat as unchanged
```

Typical epsilon range for voltage-style Y values: `1e-6` to `1e-4`.

## 4) Logging cost control

- gate noisy logs behind runtime flag
- aggregate counters once per second
- avoid string interpolation in hot loops unless enabled

## 5) Allocation guards

- preallocate render buffers
- reuse channel index arrays
- avoid LINQ in inner loops
- avoid repeated color/brush conversions inside refresh

## 6) Timing instrumentation strategy

Measure at least:
- ingest time bucket
- compute/worker bucket
- render buffer fill bucket
- plot refresh bucket

Without this split, tuning guesses are usually wrong.

## 7) Progressive degradation strategy

Under pressure, degrade in this order:
1. lower visual detail (decimation)
2. lower render FPS slightly
3. reduce non-essential overlays/labels
4. never block input handling

## 8) Guard anti-patterns

- heavy locks around whole render loop
- broad try/catch swallowing repeated failures silently
- expensive diagnostics always-on in release builds
