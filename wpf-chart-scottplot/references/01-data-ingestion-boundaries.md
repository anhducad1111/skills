# Data Ingestion Boundaries

Keep ingest robust and cheap. The chart cannot be smooth if ingest is unstable.

## 1) Transport-agnostic ingest loop

Whether data comes from UART, TCP, file replay, or shared memory, ingest should:

1. read bytes/messages
2. frame/parse
3. validate
4. normalize into chart record
5. enqueue to worker

No UI work in this loop.

## 2) Backpressure policy

Choose one explicit policy and expose telemetry.

### Option A: Drop newest when queue is full
- preserves continuity of older queued data
- can increase display lag

### Option B: Drop oldest when queue is full
- keeps chart close to real time
- sacrifices historical continuity

### Option C: Adaptive skip in producer
- parse all, enqueue sampled subset under pressure
- best when real-time view is more important than exact visual trace

Whatever policy you pick, count drops and show diagnostics.

## 3) Queue sizing

Rule of thumb:

```text
queue_capacity >= peak_ingest_rate * tolerated_lag_seconds
```

Example:
- peak 20,000 samples/s
- tolerated lag 1.5 s
- capacity >= 30,000 records

Then validate memory footprint and GC behavior.

## 4) Parser performance rules

- avoid repeated string conversions in hot path
- avoid per-frame logging by default
- use pooled buffers if payloads are large
- prefer switch-based frame-size routing over dynamic reflection

## 5) Timestamp strategy

Normalize source timestamp early and keep monotonic series:

- if source timestamp wraps/resets, detect and compensate
- if source jitter is large, smooth only for display window math
- never rewrite raw source timestamp if auditing is required

## 6) Ingest metrics you should always track

- bytes/sec or packets/sec
- valid frames/sec
- invalid frames/sec (CRC/format)
- queue depth
- queue drop count
- max parser loop duration

These metrics are often enough to diagnose 80% of chart stutter issues.

## 7) Example: bounded enqueue helper

```csharp
private readonly ConcurrentQueue<SamplePacket> _queue = new();
private int _queueDrops;
private const int MaxQueue = 50_000;

private void EnqueuePacket(SamplePacket packet)
{
    if (_queue.Count >= MaxQueue)
    {
        Interlocked.Increment(ref _queueDrops);
        return; // drop newest policy
    }
    _queue.Enqueue(packet);
}
```

For higher throughput, consider `Channel<T>` with bounded mode.

## 8) Ingest anti-patterns

- `Dispatcher.Invoke` per packet
- writing to `ObservableCollection` per packet
- `Debug.WriteLine` for every frame at high rates
- unbounded queue without any alerting

## 9) Validation tests

- synthetic burst input for 60 seconds
- cable/network flap simulation
- malformed frame injection
- sustained run with logging enabled/disabled
