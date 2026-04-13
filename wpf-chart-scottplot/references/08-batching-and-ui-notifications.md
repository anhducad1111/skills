# Batching and UI Notifications

Charts often coexist with logs, tables, and status panels.
Those UI elements can silently steal frame budget.

## 1) Batch collection updates

For high-frequency feeds, prefer range operations and single notifications.

Example idea:
- collect N items off-thread
- dispatch one batch add/reset every 50-200 ms

This dramatically reduces layout/binding churn.

## 2) Queue-first UI data flow

Pattern:
1. producer queues log/status items
2. UI timer flushes queue in chunks
3. collection enforces max size

Do not mutate UI-bound collections directly from hot path.

## 3) Notification throttling

Low-priority status labels (rate, throughput, packet counters):
- update at 2-10 Hz
- not per sample/frame

Human users cannot perceive 100+ Hz text updates, but CPU can.

## 4) Max retained items

Set limits for logs and diagnostics lists.

Example:
- retain last 2,000-10,000 entries
- remove oldest in batches, not one-by-one

## 5) ObservableCollection caution

`ObservableCollection<T>` per-item updates are expensive at scale.
Use custom batch collection or view virtualization strategies.

## 6) Hot-path string handling

- avoid constructing verbose log strings unless enabled
- store structured values first, format lazily for display if possible

## 7) Common signs of UI-notification bottleneck

- chart FPS drops only when log pane is visible
- CPU spikes with no increase in ingest rate
- GC pressure increases with text updates

## 8) Quick mitigations

- disable noisy logs by default
- increase flush interval
- reduce batch size if UI spikes, increase if dispatch overhead dominates
