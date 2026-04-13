# WPF Chart ScottPlot Skill

Portable, production-focused guidance for building high-performance WPF charts with ScottPlot under heavy real-time data load.

## Overview

This skill provides a complete playbook for chart systems that must stay responsive while processing dense, high-frequency data. It covers architecture, render-loop design, decimation, axis-aware interaction, auto-follow behavior, scrollbar synchronization, performance guards, and reusable code templates.

It is intentionally **project-independent** so you can apply it across different WPF applications.

## What's Included

### SKILL.md
Core operating model and usage rules:
- Producer -> Worker -> UI render separation
- Performance-first chart design principles
- Task routing by problem type
- Non-negotiable implementation rules
- Baseline constants and expected deliverables

### References

#### 00-portable-architecture.md
Foundational architecture for high-throughput chart pipelines:
- Stage ownership (ingest/compute/render)
- Data contracts and thread boundaries
- Lifecycle and reset strategy
- Architecture anti-patterns and verification checks

#### 01-data-ingestion-boundaries.md
Transport-agnostic ingestion strategy:
- Backpressure policy options
- Queue sizing and overflow behavior
- Parser hot-path optimization
- Ingest metrics and stress tests

#### 02-ring-buffer-and-snapshots.md
Fixed-memory history model:
- Ring-buffer indexing and wrap logic
- Snapshot contract design
- Concurrency patterns for shared history
- Reset behavior and common indexing bugs

#### 03-render-loop-and-decimation.md
Frame loop design and render-budget control:
- Deterministic render sequence
- Timer scheduling strategy
- Pixel-based decimation formulas
- Re-entrancy guards and axis update minimization

#### 04-axis-aware-zoom-pan.md
Interaction semantics for professional chart UX:
- Axis hit-testing model
- Cursor-anchored Y zoom math
- X zoom for streaming windows
- Pan behavior and mode transitions

#### 05-auto-follow-and-scrollbar-sync.md
Navigation model for live charts:
- Explicit follow/manual modes
- Scrollbar synchronization rules
- Re-entrancy protection flags
- Thumb sizing and jump/reset helpers

#### 06-performance-guards.md
High-impact safeguards:
- Dirty-state frame skip
- Axis epsilon checks
- Allocation and logging cost controls
- Progressive degradation strategy under load

#### 07-chart-ui-structure.md
Layout and binding strategy for scalable chart screens:
- Toolbar/plot/scrollbar/legend composition
- Binding boundaries for high-rate data
- Multi-view consistency guidance

#### 08-batching-and-ui-notifications.md
Throughput-safe UI update patterns:
- Batch collection updates
- Timer-based flush pipelines
- Notification throttling
- Max-retention policies for logs/tables

#### 09-tuning-checklist.md
Practical tuning workflow:
- Baseline capture
- Safe tuning order
- Decimation/FPS/buffer tradeoffs
- Stress matrix and rollout/rollback strategy

#### 10-scottplot-advanced-patterns.md
ScottPlot-specific advanced techniques:
- `Signal` vs `Scatter` tradeoffs
- Decimation variants (step/envelope/adaptive)
- Tick/axis optimization
- Overlay and multi-channel scaling strategies

#### 11-portable-code-templates.md
Copy-ready portable templates:
- Models and snapshot provider
- Scroll controller and interaction helper
- Worker loop and live view template
- ViewModel glue, XAML skeleton, ingest adapter

## When to Use This Skill

Use this skill when you need to:
- Build real-time WPF charts with ScottPlot
- Render large windows smoothly (thousands of points)
- Handle many visible channels simultaneously
- Implement robust zoom/pan/follow behavior
- Add or fix chart scrollbars for historical navigation
- Reduce CPU/memory usage in chart-heavy screens
- Create reusable chart architecture across projects

## Key Principles

1. **Separate concerns strictly** - ingest, compute, and render must be decoupled.
2. **Bound memory and work** - fixed buffers, bounded queues, fixed render cadence.
3. **Reuse everything in hot paths** - plottables, arrays, metadata caches.
4. **Decimate by pixel budget** - render what users can see, not all raw points.
5. **Keep interaction explicit** - axis-aware gestures and clear mode transitions.
6. **Guard expensive operations** - skip no-op frames and redundant axis updates.
7. **Measure before tuning** - use FPS, P95 frame time, queue depth, CPU, memory.

## Quick Start

### Recommended Read Path

1. `SKILL.md`
2. `references/00-portable-architecture.md`
3. `references/03-render-loop-and-decimation.md`
4. `references/05-auto-follow-and-scrollbar-sync.md`
5. `references/11-portable-code-templates.md`

### Minimal Integration Path

1. Copy worker + snapshot + scroll controller templates.
2. Wire data source into ingest adapter.
3. Add `WpfPlot` and scrollbar in XAML.
4. Connect render timer and interaction handlers.
5. Tune constants with `09-tuning-checklist.md`.

## Best Practices

### Do's ✅
- Pre-create and reuse ScottPlot plottables.
- Use fixed-size ring buffers for history.
- Keep chart refresh to one call per frame.
- Disable auto-follow on manual pan/drag.
- Batch non-chart UI updates (logs/tables).
- Pause render loop when chart is hidden.

### Don'ts ❌
- Parse data on UI thread.
- Rebuild plot objects every refresh.
- Update axis limits blindly every frame.
- Use unbounded queues without monitoring.
- Flood UI-bound collections per sample.
- Mix follow and manual modes implicitly.

## Troubleshooting Entry Points

- **Low FPS / stutter**: `03`, `06`, `09`, `10`
- **Zoom or pan feels wrong**: `04`, `05`, `10`
- **Memory growth / GC spikes**: `02`, `06`, `08`
- **UI lag outside chart**: `08`, `06`

## Resources

- **Core**: `SKILL.md`
- **Advanced ScottPlot**: `references/10-scottplot-advanced-patterns.md`
- **Code starters**: `references/11-portable-code-templates.md`
- **Tuning workflow**: `references/09-tuning-checklist.md`

## Tips for Success

1. Start with architecture and boundaries before visual polish.
2. Keep a stable baseline profile before each tuning pass.
3. Tune one variable group at a time.
4. Prefer deterministic behavior over clever but opaque logic.
5. Validate long-run stability, not only short demos.
6. Keep rollback-safe constants/configs for production.

---

**Note:** This skill is designed for portability. Adapt constants and templates to your hardware profile and product interaction requirements, but keep the pipeline separation and guard patterns intact.
