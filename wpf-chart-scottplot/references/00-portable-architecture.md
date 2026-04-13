# Portable Architecture

This architecture is project-agnostic and proven for high-rate charting workloads.

## 1) Three-stage chart pipeline

### Stage A: Producer (ingest)
- Runs on background thread(s)
- Receives and parses data frames/samples
- Performs basic validation and normalization
- Enqueues parsed records into a thread-safe queue

### Stage B: Worker (compute)
- Runs as long-lived background task
- Drains queue in bounded batches
- Writes into fixed-size history buffers
- Computes viewport metadata and publishes snapshots

### Stage C: UI renderer (presentation)
- Runs on `DispatcherTimer`
- Pulls latest snapshot only
- Applies decimation and axis updates
- Refreshes plot once

This separation isolates spikes and makes performance predictable.

## 2) Ownership boundaries

Keep responsibilities explicit:

- Producer owns parsing and ingestion reliability
- Worker owns history storage and viewport math
- UI owns plotting and interaction feedback

If these boundaries blur, stutter and deadlocks are common.

## 3) Data contracts between stages

Define minimal immutable contracts:

### Record contract (producer -> worker)
```csharp
public sealed record SamplePacket(
    long Sequence,
    long TimestampTicks,
    double[] ChannelValues);
```

### Snapshot contract (worker -> UI)
```csharp
public sealed record ChartSnapshot(
    int WindowStartIndex,
    int VisibleCount,
    int TotalPoints,
    int OldestIndex,
    double WindowDurationSec,
    double TotalDurationSec);
```

Keep these contracts narrow to reduce coupling.

## 4) Threading model

Recommended primitives:

- `ConcurrentQueue<T>` or `Channel<T>` for producer/worker handoff
- `ReaderWriterLockSlim` or lock-free copy model for shared history access
- `CancellationTokenSource` for lifecycle control
- `DispatcherTimer` for render cadence

Avoid blocking UI thread waits (`Wait`, `.Result`, etc).

## 5) Event-rate control

Your app can receive data faster than you should render.

Design rules:
- Ingest at source speed
- Compute in bounded chunks
- Render at fixed human-meaningful cadence

A good chart shows stable motion, not every micro-update.

## 6) Lifecycle and visibility

When chart tab/page is hidden:
- stop or slow render timer
- keep compute alive only if required by app behavior

When chart returns visible:
- resume render timer
- pick latest snapshot and render from current state

Never try to “replay all missed frames” on UI.

## 7) Failure strategy

Support controlled reset:
- clear queue
- reset ring buffers
- publish empty snapshot
- keep services alive for reconnect

A reliable reset path is essential for long-running dashboards.

## 8) Architecture anti-patterns

- producer writes directly into UI controls
- worker holding long write locks during large loops
- UI thread parsing or decoding transport frames
- queue without max depth policy
- chart refresh called from multiple uncontrolled threads

## 9) Architecture verification checklist

- UI remains responsive while ingest rate doubles
- chart FPS remains near target under sustained load
- no unbounded memory growth in 30+ minute run
- no exceptions during reconnect/reset cycles
