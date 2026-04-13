# Tuning Checklist

Use this checklist to tune any WPF + ScottPlot chart workload.

## 1) Establish baseline first

Before changes, capture:
- average render FPS
- P95 frame time
- CPU usage of process
- memory (working set + GC heaps)
- queue depth trend

Run baseline for at least 2-5 minutes under representative load.

## 2) Tune in safe order

Order matters. Start with highest leverage, lowest risk.

1. Decimation constants
2. Render FPS target
3. Axis-update guards
4. UI notification throttling
5. Buffer capacities

Change one group at a time.

## 3) Decimation tuning table

| Goal | Change | Risk |
| --- | --- | --- |
| Lower CPU | decrease `maxPts` | less visual detail |
| More detail | increase `maxPts` | higher frame cost |
| Smoother scaling | tune `pointsPerPixel` | may alter visual density |

## 4) FPS target tuning

Typical targets:
- 20 FPS: low CPU, still usable for slow-changing signals
- 24 FPS: good compromise for mid hardware
- 30 FPS: common sweet spot for responsive dashboards

Above 30 FPS usually has diminishing returns in desktop telemetry apps.

## 5) Buffer capacity tuning

Higher history capacity:
- more browseable history in-memory
- potentially larger worker/lookup cost

Lower capacity:
- lower memory and sometimes lower compute
- less immediate history window

Choose by product needs, not by guesswork.

## 6) Pan and zoom feel tuning

- pan ratio too high -> jumpy navigation
- pan ratio too low -> sluggish navigation
- start around `0.08` and adjust by user testing

For Y zoom, ensure cursor-anchor math is stable and clamped.

## 7) Stress scenarios to test every time

1. all channels visible
2. rapid channel visibility toggling
3. repeated zoom/pan while data streams
4. freeze/unfreeze cycles
5. disconnect/reconnect and hard reset
6. long run (30-60 min)

## 8) Pass/fail criteria template

Define concrete thresholds, for example:
- FPS >= 24 for 95% of test duration
- CPU <= 20% on target machine
- no sustained queue growth
- no unhandled exceptions
- no visible input lag > 100 ms

## 9) Troubleshooting map

Symptom -> likely cause:

- periodic stutter every few seconds -> GC or batched heavy UI update
- constant low FPS with low queue depth -> render path too heavy
- queue grows while FPS stable -> worker bottleneck
- UI clicks lag but FPS looks fine -> timer priority or dispatcher contention

## 10) Rollout strategy

When deploying tuning changes:
- expose critical constants via config where safe
- keep old profile available for rollback
- compare metrics in same workload scenario

Good tuning is iterative, measured, and reversible.
