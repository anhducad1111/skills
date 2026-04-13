# Ring Buffer and Snapshots

This is the core for large-data chart stability.

## 1) Why ring buffers win

For continuous streams, ring buffers provide:
- fixed memory ceiling
- O(1) append behavior
- predictable cache-friendly access

Compared to growing lists, they avoid allocation churn and trimming overhead.

## 2) Suggested history layout

Channel-major layout works well for per-channel rendering:

```csharp
private readonly double[][] _historyY;
private readonly long[] _timelineTicks;
private int _writeIndex;
private int _totalPoints;
private readonly int _capacity;
```

Initialize once and never resize in hot path.

## 3) Absolute index to ring index mapping

When full, oldest sample starts at `_writeIndex`.

```csharp
int oldest = _totalPoints < _capacity ? 0 : _writeIndex;
int bufIdx = (oldest + absIndex) % _capacity;
```

This mapping must be consistent across worker and renderer.

## 4) Worker write algorithm

Per incoming packet:

1. write all channel values to `_historyY[ch][_writeIndex]`
2. write timestamp to `_timelineTicks[_writeIndex]`
3. increment `_writeIndex = (_writeIndex + 1) % capacity`
4. increment `_totalPoints` until it reaches capacity

Keep this loop tight and allocation-free.

## 5) Snapshot pattern

UI should consume metadata, not copied history arrays.

Minimal snapshot fields:
- visible window start index
- visible count
- total points
- oldest index
- duration info

Optional fields:
- x-axis label summary
- data staleness flag
- worker cycle id

## 6) Concurrency patterns

Two good options:

### Option A: Shared buffers + locks
- worker writes under write lock
- UI reads under read lock
- simple and explicit

### Option B: double-buffer snapshots
- worker copies only metadata, not full arrays
- UI reads atomically swapped references
- more complex but reduces lock contention

For most desktop dashboards, Option A is sufficient.

## 7) Window calculation strategy

In follow mode:
- compute window based on newest timestamp and desired duration
- use binary search on timeline for start index

In manual mode:
- keep user-selected start index
- clamp to valid range as total points changes

## 8) Reset behavior

Define explicit hard reset path:
- clear queue
- clear ring arrays (if required)
- zero counters and indices
- publish empty snapshot

Do not leave stale `oldest`/`write` combinations.

## 9) Memory estimation quick formula

```text
memory_bytes ~= channels * capacity * sizeof(double)
             + capacity * sizeof(long)
             + overhead
```

Example:
- 25 channels, capacity 4000
- data only: 25 * 4000 * 8 = 800,000 bytes (~0.76 MB)
- timeline: 4000 * 8 = 32,000 bytes
- total still comfortably low before overhead.

## 10) Common bugs

- off-by-one in visible end index
- forgetting wrap-around on timeline lookup
- stale snapshot after reset
- long lock durations during batch copy
