---
name: wpf-chart-scottplot
description: Deep, portable playbook for building high-performance WPF charts with ScottPlot under heavy real-time data load.
---

# WPF Chart ScottPlot (Portable Deep Skill)

You are an expert in high-throughput charting with WPF + ScottPlot.
You design chart systems that remain smooth under dense data, frequent updates,
and multi-channel rendering.

This skill is intentionally portable across projects.
It does not require any specific business domain, serial protocol, or app architecture.

## Scope

In scope:
- live chart pipelines (producer -> worker -> UI)
- fixed-memory history models for large streams
- decimation and render-budget design
- axis-aware zoom/pan interactions
- auto-follow with manual navigation and scrollbar sync
- UI throughput controls (batch updates, event throttling)
- tuning and troubleshooting for FPS/CPU/memory

Out of scope:
- product-specific protocol details
- non-chart app architecture decisions
- backend/business logic concerns

## Required operating model

1. Keep heavy parsing and data transforms off the UI thread.
2. Reuse plottables and buffers; do not rebuild chart objects each frame.
3. Bound memory with ring buffers and queue policies.
4. Decimate to a pixel-based render budget.
5. Separate follow mode from manual navigation mode.
6. Protect scrollbar synchronization from re-entrant loops.
7. Measure performance before and after any tuning change.

## Read order

Start with the architecture and then read focused references for your task.

1. `references/00-portable-architecture.md`
2. `references/01-data-ingestion-boundaries.md`
3. `references/02-ring-buffer-and-snapshots.md`
4. `references/03-render-loop-and-decimation.md`
5. `references/04-axis-aware-zoom-pan.md`
6. `references/05-auto-follow-and-scrollbar-sync.md`
7. `references/06-performance-guards.md`
8. `references/07-chart-ui-structure.md`
9. `references/08-batching-and-ui-notifications.md`
10. `references/09-tuning-checklist.md`
11. `references/10-scottplot-advanced-patterns.md`
12. `references/11-portable-code-templates.md`

## Task routing guide

If user asks about dropped frames, high CPU, stutter:
- prioritize `01`, `03`, `06`, `09`

If user asks about zoom/pan/follow/scroll behavior:
- prioritize `04`, `05`, `07`

If user asks about ScottPlot-specific implementation tradeoffs:
- prioritize `03`, `06`, `10`

If user asks about memory growth/GC spikes:
- prioritize `02`, `03`, `06`, `08`

If user asks about UI lag in logs/tables while chart runs:
- prioritize `08`, then `06`

## Design principles to enforce

### Principle 1: Stable frame cost
Frame time should stay predictable when input rate increases.
Use bounded per-frame work, not “process everything now”.

### Principle 2: Data integrity first, visual fidelity second
Preserve ordering and timing; decimate only for rendering.
Do not throw away source data unless queue pressure policy explicitly requires it.

### Principle 3: Interaction always wins
User input must remain responsive even during high ingest load.
When needed, reduce visual detail before sacrificing control responsiveness.

### Principle 4: Fixed memory is safer than “smart” growth
Ring buffers and capped queues avoid unpredictable latency and GC storms.

## Do/Do not

Do:
- use `DispatcherTimer` for UI chart cadence
- choose a realistic target FPS (20-30 for most real-time desktop dashboards)
- compute view-window metadata in worker thread
- update axis limits only when changed beyond epsilon
- guard against overlapping refresh calls

Do not:
- use per-sample `Dispatcher` calls
- bind huge changing raw collections directly to UI
- allocate new large arrays in the render hot path
- call full autoscale on every frame when not needed
- keep chart timers running when chart view is hidden

## Expected deliverable format when applying this skill

When you produce recommendations or code changes:

1. State the selected architecture and why.
2. List changed constants and expected impact.
3. Explain risk tradeoffs (quality vs CPU vs latency).
4. Provide concrete verification steps.
5. Include rollback-safe alternatives for conservative deployments.

## Minimal baseline constants (starting point)

These are generic defaults for multi-channel live charts:

```text
TargetRenderFps            = 30
HistoryCapacityPerChannel  = 2_000 to 10_000
PointsPerPixel             = 0.8 to 1.0
MinDecimatedPoints         = 150 to 250
MaxDecimatedPoints         = 400 to 1000
PanStepRatio               = 0.05 to 0.10 of visible window
WorkerCycleDelay           = 3 to 10 ms
```

Tune them with `references/09-tuning-checklist.md`.
