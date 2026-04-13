# Portable Code Templates

This file provides copy-ready templates you can adapt to any WPF + ScottPlot project.

Goal:
- portable structure
- predictable performance
- clear ownership boundaries

The templates below intentionally omit business/domain details.

---

## 1) Core models

```csharp
namespace MyApp.Charting;

public sealed record SamplePacket(
    long Sequence,
    long SourceTimestampTicks,
    double[] Values);

public sealed class ChartSnapshot
{
    public int WindowStartIndex { get; init; }
    public int VisibleCount { get; init; }
    public int TotalPoints { get; init; }
    public int OldestIndex { get; init; }
    public int WriteIndex { get; init; }
    public double WindowDurationSec { get; init; }
    public double TotalDurationSec { get; init; }
    public string XRangeText { get; init; } = string.Empty;
}
```

---

## 2) Snapshot provider

```csharp
using System.Threading;

namespace MyApp.Charting;

public sealed class ChartSnapshotProvider
{
    private ChartSnapshot _current = new();
    private readonly ReaderWriterLockSlim _lock = new();

    public void Publish(ChartSnapshot snapshot)
    {
        _lock.EnterWriteLock();
        try { _current = snapshot; }
        finally { _lock.ExitWriteLock(); }
    }

    public ChartSnapshot Get()
    {
        _lock.EnterReadLock();
        try { return _current; }
        finally { _lock.ExitReadLock(); }
    }
}
```

---

## 3) Scroll/navigation controller

```csharp
using System;
using System.Windows;
using System.Windows.Controls.Primitives;

namespace MyApp.Charting;

public sealed class ChartScrollController
{
    private int _windowStart;
    private bool _isUpdatingScrollbar;
    private bool _isUpdatingFromScrollbar;
    private const double PanRatio = 0.08;

    public int WindowStart => _windowStart;
    public event Action<int>? WindowStartChanged;

    public void OnScrollBarDrag(double value)
    {
        if (_isUpdatingScrollbar || _isUpdatingFromScrollbar) return;
        _isUpdatingFromScrollbar = true;
        try
        {
            _windowStart = Math.Max(0, (int)Math.Round(value));
            WindowStartChanged?.Invoke(_windowStart);
        }
        finally
        {
            _isUpdatingFromScrollbar = false;
        }
    }

    public void PanX(int direction, int visibleCount, int totalPoints)
    {
        int step = Math.Max(1, (int)(visibleCount * PanRatio));
        int maxStart = Math.Max(0, totalPoints - visibleCount);
        _windowStart = direction > 0
            ? Math.Min(maxStart, _windowStart + step)
            : Math.Max(0, _windowStart - step);
        WindowStartChanged?.Invoke(_windowStart);
    }

    public void JumpToEnd(int totalPoints, int visibleCount)
    {
        _windowStart = Math.Max(0, totalPoints - visibleCount);
        WindowStartChanged?.Invoke(_windowStart);
    }

    public void Reset()
    {
        _windowStart = 0;
        WindowStartChanged?.Invoke(_windowStart);
    }

    public void Clamp(int totalPoints, int visibleCount)
    {
        int maxStart = Math.Max(0, totalPoints - visibleCount);
        _windowStart = Math.Clamp(_windowStart, 0, maxStart);
    }

    public void UpdatePositionSilently(int newPosition)
    {
        _windowStart = Math.Max(0, newPosition);
    }

    public void UpdateScrollBarUI(RangeBase bar, int total, int visible, double windowSec = 0, double totalSec = 0)
    {
        if (_isUpdatingFromScrollbar) return;
        _isUpdatingScrollbar = true;
        try
        {
            int maxStart = Math.Max(0, total - visible);
            if (maxStart <= 0)
            {
                bar.Visibility = Visibility.Collapsed;
                return;
            }

            bar.Visibility = Visibility.Visible;
            bar.Minimum = 0;
            bar.Maximum = maxStart;
            bar.SmallChange = Math.Max(1, visible / 20);

            if (bar is ScrollBar sb && windowSec > 0 && totalSec > 0)
            {
                double ratio = windowSec / totalSec;
                sb.ViewportSize = Math.Clamp(ratio * maxStart, 1, maxStart);
            }
            else
            {
                bar.LargeChange = Math.Max(1, visible);
            }

            bar.Value = Math.Clamp(_windowStart, 0, maxStart);
        }
        finally
        {
            _isUpdatingScrollbar = false;
        }
    }
}
```

---

## 4) Interaction helper (axis hit-test + cursor Y zoom)

```csharp
using System;
using System.Windows;
using ScottPlot.WPF;

namespace MyApp.Charting;

public enum AxisTarget
{
    ChartArea,
    XAxis,
    YAxis
}

public static class ChartInteractionHelper
{
    public static AxisTarget GetAxisTarget(WpfPlot? plot, Point mouse)
    {
        if (plot?.ActualWidth <= 0 || plot?.ActualHeight <= 0)
            return AxisTarget.ChartArea;

        try
        {
            var last = plot.Plot.RenderManager.LastRender;
            if (last == null) return AxisTarget.ChartArea;

            var rect = last.DataRect;
            double x = mouse.X;
            double y = mouse.Y;

            double xAxisTop = rect.Bottom;
            double xAxisBottom = rect.Bottom + 30;
            if (y >= xAxisTop && y <= xAxisBottom && x >= rect.Left && x <= rect.Right)
                return AxisTarget.XAxis;

            if (x < rect.Left && y >= rect.Top && y <= rect.Bottom)
                return AxisTarget.YAxis;

            return AxisTarget.ChartArea;
        }
        catch
        {
            return AxisTarget.ChartArea;
        }
    }

    public static void ZoomYAtCursor(WpfPlot? plot, double zoomFactor, int cursorPixelY, ref double? yMin, ref double? yMax)
    {
        if (plot == null) return;
        if (!yMin.HasValue || !yMax.HasValue)
        {
            var lim = plot.Plot.Axes.GetLimits();
            yMin = lim.Bottom;
            yMax = lim.Top;
        }

        try
        {
            var last = plot.Plot.RenderManager.LastRender;
            if (last == null) return;
            var rect = last.DataRect;
            double h = rect.Bottom - rect.Top;
            if (h <= 0) return;

            double p = (cursorPixelY - rect.Top) / h;
            p = Math.Clamp(p, 0.0, 1.0);

            double range = yMax.Value - yMin.Value;
            double yAtCursor = yMax.Value - p * range;
            double newRange = range / zoomFactor;

            yMin = yAtCursor - (1.0 - p) * newRange;
            yMax = yAtCursor + p * newRange;

            plot.Plot.Axes.SetLimitsY(yMin.Value, yMax.Value);
            plot.Refresh();
        }
        catch
        {
            // ignore when render state unavailable
        }
    }
}
```

---

## 5) Worker (queue -> ring buffer -> snapshot)

```csharp
using System;
using System.Collections.Concurrent;
using System.Threading;
using System.Threading.Tasks;

namespace MyApp.Charting;

public sealed class ChartWorker
{
    private readonly ConcurrentQueue<SamplePacket> _queue;
    private readonly ChartSnapshotProvider _snapshots;
    private readonly ReaderWriterLockSlim _historyLock = new();

    private readonly int _channels;
    private readonly int _capacity;
    private readonly double[][] _history;
    private readonly DateTime[] _timeline;

    private int _writeIndex;
    private int _totalPoints;
    private int _manualWindowStart;

    public bool AutoFollowLatest { get; set; } = true;
    public bool FreezeIngest { get; set; }
    public double WindowSeconds { get; set; } = 5.0;
    public double MinWindowSeconds { get; set; } = 0.5;
    public double MaxWindowSeconds { get; set; } = 60.0;

    public ChartWorker(ConcurrentQueue<SamplePacket> queue, ChartSnapshotProvider snapshots, int channels = 25, int capacity = 4000)
    {
        _queue = queue;
        _snapshots = snapshots;
        _channels = channels;
        _capacity = capacity;
        _history = new double[_channels][];
        for (int i = 0; i < _channels; i++)
            _history[i] = new double[_capacity];
        _timeline = new DateTime[_capacity];
    }

    public (double[][] History, DateTime[] Timeline) AcquireHistoryReadOnly()
    {
        _historyLock.EnterReadLock();
        try { return (_history, _timeline); }
        finally { _historyLock.ExitReadLock(); }
    }

    public void SetManualWindowStart(int value) => _manualWindowStart = Math.Max(0, value);

    public async Task RunAsync(CancellationToken token)
    {
        const int MaxPacketsPerCycle = 1000;

        while (!token.IsCancellationRequested)
        {
            try
            {
                if (!FreezeIngest)
                {
                    int consumed = 0;
                    while (consumed < MaxPacketsPerCycle && _queue.TryDequeue(out SamplePacket? pkt))
                    {
                        DateTime ts = pkt.SourceTimestampTicks > 0
                            ? new DateTime(pkt.SourceTimestampTicks, DateTimeKind.Utc)
                            : DateTime.UtcNow;

                        _historyLock.EnterWriteLock();
                        try
                        {
                            for (int ch = 0; ch < _channels; ch++)
                                _history[ch][_writeIndex] = pkt.Values[ch];

                            _timeline[_writeIndex] = ts;
                            _writeIndex = (_writeIndex + 1) % _capacity;
                            if (_totalPoints < _capacity) _totalPoints++;
                        }
                        finally
                        {
                            _historyLock.ExitWriteLock();
                        }

                        consumed++;
                    }
                }

                int visible = ComputeVisibleCount();
                int oldest = _totalPoints < _capacity ? 0 : _writeIndex;
                int maxStart = Math.Max(0, _totalPoints - visible);
                int start = AutoFollowLatest ? maxStart : Math.Min(_manualWindowStart, maxStart);

                (double windowSec, double totalSec, string label) = ComputeDurations(start, visible, oldest);

                _snapshots.Publish(new ChartSnapshot
                {
                    WindowStartIndex = start,
                    VisibleCount = visible,
                    TotalPoints = _totalPoints,
                    OldestIndex = oldest,
                    WriteIndex = _writeIndex,
                    WindowDurationSec = windowSec,
                    TotalDurationSec = totalSec,
                    XRangeText = label
                });

                await Task.Delay(5, token);
            }
            catch (OperationCanceledException)
            {
                break;
            }
            catch
            {
                await Task.Delay(10, token);
            }
        }
    }

    private int ComputeVisibleCount()
    {
        if (_totalPoints == 0) return 500;

        double sec = Math.Clamp(WindowSeconds, MinWindowSeconds, MaxWindowSeconds);
        int sampleSize = Math.Min(100, _totalPoints);
        if (sampleSize < 2) return Math.Max(1, (int)(sec * 20));

        int oldest = _totalPoints < _capacity ? 0 : _writeIndex;
        int newest = (_writeIndex - 1 + _capacity) % _capacity;
        int sampleStart = (newest - sampleSize + 1 + _capacity) % _capacity;

        DateTime t0 = _timeline[sampleStart];
        DateTime t1 = _timeline[newest];
        double d = (t1 - t0).TotalSeconds;
        if (d <= 0) return Math.Max(1, (int)(sec * 20));

        double pps = sampleSize / d;
        int est = (int)(pps * sec);
        return Math.Clamp(est, 1, _totalPoints);
    }

    private (double windowSec, double totalSec, string label) ComputeDurations(int start, int visible, int oldest)
    {
        if (_totalPoints <= 0) return (0, 0, string.Empty);

        int end = Math.Min(_totalPoints - 1, start + visible - 1);
        int startBuf = (oldest + start) % _capacity;
        int endBuf = (oldest + end) % _capacity;
        int newestBuf = (_writeIndex - 1 + _capacity) % _capacity;

        DateTime tStart = _timeline[startBuf];
        DateTime tEnd = _timeline[endBuf];
        DateTime tOldest = _timeline[oldest];
        DateTime tNewest = _timeline[newestBuf];

        double w = (tEnd - tStart).TotalSeconds;
        double total = (tNewest - tOldest).TotalSeconds;
        string text = $"{tStart:HH:mm:ss.fff} - {tEnd:HH:mm:ss.fff} ({w:F2}s)";
        return (w, total, text);
    }
}
```

---

## 6) Live chart view template (`UserControl` code-behind)

```csharp
using System;
using System.Diagnostics;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Controls.Primitives;
using System.Windows.Input;
using System.Windows.Threading;
using ScottPlot;
using ScottPlot.Plottables;
using ScottPlot.TickGenerators;
using ScottPlot.WPF;

namespace MyApp.Charting;

public partial class LiveChartView : UserControl
{
    private const int Channels = 25;
    private const int MaxHistoryPoints = 4000;
    private const double TargetRenderFps = 30.0;
    private const double PointsPerPixel = 0.9;
    private const int MinDecimatedPoints = 180;
    private const int MaxDecimatedPoints = 480;
    private const double AxisEpsilon = 1e-5;

    private readonly DispatcherTimer _timer;
    private readonly ChartScrollController _scroll = new();

    private Signal[]? _signals;
    private double[][]? _renderY;
    private readonly int[] _visibleIndices = new int[Channels];

    private bool _isRefreshing;
    private bool _refreshPending;
    private bool _userInteractionPending;

    private int _lastXStart = int.MinValue;
    private int _lastXEnd = int.MinValue;
    private double _lastYMin = double.NaN;
    private double _lastYMax = double.NaN;

    private int _lastTotal = -1;
    private int _lastWindowStart;
    private int _lastVisibleCount;
    private int _lastOldest;
    private uint _lastMask;

    private double? _manualYMin;
    private double? _manualYMax;

    // Provide these from your ViewModel/service wiring
    public required ChartSnapshotProvider SnapshotProvider { get; init; }
    public required Func<(double[][] History, DateTime[] Timeline)> AcquireHistory { get; init; }
    public required Func<bool[]> GetChannelVisible { get; init; }
    public required Action<int> SetManualWindowStart { get; init; }
    public required Action<bool> SetAutoFollow { get; init; }
    public required Func<bool> GetAutoScaleY { get; init; }
    public required Func<bool> GetFreezeRender { get; init; }
    public required Action<double> SetWindowSeconds { get; init; }
    public required Func<double> GetWindowSeconds { get; init; }

    public LiveChartView()
    {
        InitializeComponent();

        Plot.Plot.Title("Live Data");
        Plot.Plot.XLabel("Time");
        Plot.Plot.YLabel("Value");
        Plot.Plot.Legend.IsVisible = false;
        Plot.Plot.Axes.AntiAlias(false);
        Plot.UserInputProcessor.IsEnabled = false;

        var ticks = new NumericAutomatic();
        ticks.LabelFormatter = v => v.ToString("F0");
        Plot.Plot.Axes.Bottom.TickGenerator = ticks;

        InitializeSeries();

        _scroll.WindowStartChanged += idx =>
        {
            _userInteractionPending = true;
            SetManualWindowStart(idx);
        };

        _timer = new DispatcherTimer(DispatcherPriority.Input)
        {
            Interval = TimeSpan.FromMilliseconds(1000.0 / TargetRenderFps)
        };
        _timer.Tick += (_, _) => RefreshPlot();
        _timer.Start();
    }

    private void InitializeSeries()
    {
        Plot.Plot.Clear();
        _signals = new Signal[Channels];
        _renderY = new double[Channels][];

        for (int i = 0; i < Channels; i++)
        {
            _renderY[i] = new double[10_000];
            Signal sig = Plot.Plot.Add.Signal(_renderY[i]);
            sig.MaximumMarkerSize = 0;
            sig.LineWidth = 1.2f;
            sig.MinRenderIndex = 0;
            sig.MaxRenderIndex = 0;
            _signals[i] = sig;
        }
        Plot.Refresh();
    }

    private void RefreshPlot()
    {
        if (_signals == null || _renderY == null) return;

        if (_isRefreshing)
        {
            _refreshPending = true;
            return;
        }

        if (GetFreezeRender() && !_userInteractionPending)
            return;

        ChartSnapshot snap = SnapshotProvider.Get();
        if (snap.TotalPoints <= 0) return;

        uint mask = BuildVisibilityMask();
        bool autoY = GetAutoScaleY();

        if (!autoY
            && snap.TotalPoints == _lastTotal
            && snap.WindowStartIndex == _lastWindowStart
            && snap.VisibleCount == _lastVisibleCount
            && snap.OldestIndex == _lastOldest
            && mask == _lastMask)
        {
            return;
        }

        _isRefreshing = true;
        _userInteractionPending = false;

        try
        {
            (double[][] history, _) = AcquireHistory();

            int visibleChannels = 0;
            bool[] vis = GetChannelVisible();
            for (int i = 0; i < Channels; i++)
            {
                bool show = vis[i];
                if (show) _visibleIndices[visibleChannels++] = i;
                _signals[i].IsVisible = show;
            }

            if (visibleChannels == 0)
            {
                for (int i = 0; i < Channels; i++)
                {
                    _signals[i].MinRenderIndex = 0;
                    _signals[i].MaxRenderIndex = 0;
                }
                Plot.Refresh();
                CommitDirty(snap, mask);
                return;
            }

            int xStart = snap.WindowStartIndex;
            int xEnd = Math.Min(snap.TotalPoints - 1, xStart + snap.VisibleCount - 1);
            int actualVisible = Math.Max(1, xEnd - xStart + 1);

            int decimationTarget = GetDecimationTarget();
            int factor = Math.Max(1, actualVisible / decimationTarget);

            int oldest = snap.OldestIndex;
            int k = 0;
            double minY = double.MaxValue;
            double maxY = double.MinValue;

            for (int abs = xStart; abs <= xEnd; abs += factor)
            {
                if (k >= _renderY[0].Length) break;
                int buf = (oldest + abs) % MaxHistoryPoints;

                for (int vi = 0; vi < visibleChannels; vi++)
                {
                    int ch = _visibleIndices[vi];
                    double v = history[ch][buf];
                    _renderY[ch][k] = v;
                    if (v < minY) minY = v;
                    if (v > maxY) maxY = v;
                }
                k++;
            }

            if (k == 0) return;

            int last = k - 1;
            for (int ch = 0; ch < Channels; ch++)
            {
                Signal sig = _signals[ch];
                sig.Data.XOffset = xStart;
                sig.Data.Period = factor;
                sig.MinRenderIndex = 0;
                sig.MaxRenderIndex = last;
            }

            if (xStart != _lastXStart || xEnd != _lastXEnd)
            {
                Plot.Plot.Axes.SetLimitsX(xStart, xEnd);
                _lastXStart = xStart;
                _lastXEnd = xEnd;
            }

            (double yLo, double yHi) = ComputeYLimits(autoY, minY, maxY);
            if (double.IsNaN(_lastYMin)
                || double.IsNaN(_lastYMax)
                || Math.Abs(yLo - _lastYMin) > AxisEpsilon
                || Math.Abs(yHi - _lastYMax) > AxisEpsilon)
            {
                Plot.Plot.Axes.SetLimitsY(yLo, yHi);
                _lastYMin = yLo;
                _lastYMax = yHi;
            }

            _scroll.UpdatePositionSilently(snap.WindowStartIndex);
            _scroll.Clamp(snap.TotalPoints, snap.VisibleCount);
            _scroll.UpdateScrollBarUI(HorizontalScrollBar, snap.TotalPoints, snap.VisibleCount, snap.WindowDurationSec, snap.TotalDurationSec);

            CommitDirty(snap, mask);
            Plot.Refresh();
        }
        finally
        {
            _isRefreshing = false;
            if (_refreshPending)
            {
                _refreshPending = false;
                Dispatcher.BeginInvoke(DispatcherPriority.Input, RefreshPlot);
            }
        }
    }

    private void CommitDirty(ChartSnapshot s, uint mask)
    {
        _lastTotal = s.TotalPoints;
        _lastWindowStart = s.WindowStartIndex;
        _lastVisibleCount = s.VisibleCount;
        _lastOldest = s.OldestIndex;
        _lastMask = mask;
    }

    private uint BuildVisibilityMask()
    {
        bool[] vis = GetChannelVisible();
        uint m = 0;
        for (int i = 0; i < Math.Min(32, vis.Length); i++)
            if (vis[i]) m |= (1u << i);
        return m;
    }

    private int GetDecimationTarget()
    {
        int w = (int)Math.Round(Plot.ActualWidth);
        if (w < 2) return 340;
        int target = (int)Math.Round(w * PointsPerPixel);
        return Math.Clamp(target, MinDecimatedPoints, MaxDecimatedPoints);
    }

    private (double yLo, double yHi) ComputeYLimits(bool autoY, double minY, double maxY)
    {
        if (autoY)
        {
            double r = Math.Max(0.2, maxY - minY);
            double p = r * 0.04 + 0.01;
            _manualYMin = null;
            _manualYMax = null;
            return (minY - p, maxY + p);
        }

        if (!_manualYMin.HasValue || !_manualYMax.HasValue)
        {
            double r = Math.Max(0.2, maxY - minY);
            double p = r * 0.04 + 0.01;
            _manualYMin = minY - p;
            _manualYMax = maxY + p;
        }
        return (_manualYMin.Value, _manualYMax.Value);
    }

    // Wire this to WpfPlot MouseWheel
    private void Plot_MouseWheel(object sender, MouseWheelEventArgs e)
    {
        AxisTarget target = ChartInteractionHelper.GetAxisTarget(Plot, e.GetPosition(Plot));
        bool ctrl = (Keyboard.Modifiers & ModifierKeys.Control) != 0;
        bool zoomIn = e.Delta > 0;
        ChartSnapshot snap = SnapshotProvider.Get();

        switch (target)
        {
            case AxisTarget.XAxis:
                {
                    double win = GetWindowSeconds();
                    double next = win * (zoomIn ? 0.8 : 1.25);
                    SetWindowSeconds(next);
                    _userInteractionPending = true;
                    e.Handled = true;
                    break;
                }
            case AxisTarget.YAxis:
                {
                    ChartInteractionHelper.ZoomYAtCursor(Plot, zoomIn ? 1.25 : 0.8, (int)e.GetPosition(Plot).Y, ref _manualYMin, ref _manualYMax);
                    e.Handled = true;
                    break;
                }
            case AxisTarget.ChartArea when ctrl:
                {
                    _scroll.PanX(zoomIn ? -1 : 1, snap.VisibleCount, snap.TotalPoints);
                    SetAutoFollow(false);
                    e.Handled = true;
                    break;
                }
        }
    }

    // Wire this to ScrollBar.Scroll
    private void HorizontalScrollBar_Scroll(object sender, ScrollEventArgs e)
    {
        _scroll.OnScrollBarDrag(e.NewValue);
        SetAutoFollow(false);
    }

    // Wire this to WpfPlot.MouseDoubleClick
    private void Plot_MouseDoubleClick(object sender, MouseButtonEventArgs e)
    {
        ChartSnapshot s = SnapshotProvider.Get();
        SetAutoFollow(true);
        _manualYMin = null;
        _manualYMax = null;
        _scroll.JumpToEnd(s.TotalPoints, s.VisibleCount);
        e.Handled = true;
    }
}
```

---

## 7) ViewModel glue template

```csharp
using System.Collections.Concurrent;
using System.Threading;
using System.Threading.Tasks;

namespace MyApp.Charting;

public sealed class ChartViewModel
{
    private readonly ConcurrentQueue<SamplePacket> _queue = new();
    private readonly ChartSnapshotProvider _snapshots = new();
    private readonly ChartWorker _worker;
    private CancellationTokenSource? _cts;

    public bool AutoFollowLatest
    {
        get => _worker.AutoFollowLatest;
        set => _worker.AutoFollowLatest = value;
    }

    public bool FreezeData
    {
        get => _worker.FreezeIngest;
        set => _worker.FreezeIngest = value;
    }

    public double WindowSeconds
    {
        get => _worker.WindowSeconds;
        set => _worker.WindowSeconds = value;
    }

    public ChartSnapshotProvider SnapshotProvider => _snapshots;

    public ChartViewModel()
    {
        _worker = new ChartWorker(_queue, _snapshots, channels: 25, capacity: 4000);
    }

    public void Start()
    {
        _cts = new CancellationTokenSource();
        _ = Task.Run(() => _worker.RunAsync(_cts.Token));
    }

    public void Stop()
    {
        _cts?.Cancel();
    }

    public void PushSample(SamplePacket packet)
    {
        _queue.Enqueue(packet);
    }

    public (double[][] History, DateTime[] Timeline) AcquireHistory() => _worker.AcquireHistoryReadOnly();

    public void SetManualWindowStart(int value) => _worker.SetManualWindowStart(value);
}
```

---

## 8) XAML template (`LiveChartView.xaml`)

```xml
<UserControl x:Class="MyApp.Charting.LiveChartView"
             xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
             xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
             xmlns:ScottPlot="clr-namespace:ScottPlot.WPF;assembly=ScottPlot.WPF">
    <DockPanel>
        <Border DockPanel.Dock="Top" Padding="6,4">
            <StackPanel Orientation="Horizontal">
                <TextBlock Text="Window:" VerticalAlignment="Center"/>
                <ComboBox Width="90" Margin="6,0,0,0"/>
                <CheckBox Content="Auto Y" Margin="12,0,0,0"/>
                <CheckBox Content="Freeze" Margin="8,0,0,0"/>
            </StackPanel>
        </Border>

        <Grid>
            <Grid.RowDefinitions>
                <RowDefinition Height="*"/>
                <RowDefinition Height="Auto"/>
            </Grid.RowDefinitions>

            <ScottPlot:WpfPlot x:Name="Plot"
                               Grid.Row="0"
                               MouseWheel="Plot_MouseWheel"
                               MouseDoubleClick="Plot_MouseDoubleClick"/>

            <ScrollBar x:Name="HorizontalScrollBar"
                       Grid.Row="1"
                       Orientation="Horizontal"
                       Height="16"
                       Visibility="Collapsed"
                       Scroll="HorizontalScrollBar_Scroll"/>
        </Grid>
    </DockPanel>
</UserControl>
```

---

## 9) Ingest adapter template (transport-agnostic)

```csharp
namespace MyApp.Charting;

public sealed class ChartIngestAdapter
{
    private readonly ChartViewModel _vm;
    private long _seq;

    public ChartIngestAdapter(ChartViewModel vm)
    {
        _vm = vm;
    }

    // Call this from UART/TCP/file parser callback
    public void OnValues(long sourceTimestampTicks, double[] values)
    {
        if (values.Length < 25) return;
        // clone only if caller reuses mutable buffer
        double[] copy = (double[])values.Clone();
        _vm.PushSample(new SamplePacket(_seq++, sourceTimestampTicks, copy));
    }
}
```

---

## 10) Optional: batch collection template for log panes

```csharp
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Collections.Specialized;

namespace MyApp.Charting;

public sealed class BatchObservableCollection<T> : ObservableCollection<T>
{
    public void AddRange(IEnumerable<T> items)
    {
        foreach (T item in items)
            Items.Add(item);

        OnCollectionChanged(new NotifyCollectionChangedEventArgs(NotifyCollectionChangedAction.Reset));
    }

    public void RemoveRange(int index, int count)
    {
        if (count <= 0) return;
        int actual = System.Math.Min(count, Items.Count - index);
        if (actual <= 0) return;

        ((List<T>)Items).RemoveRange(index, actual);
        OnCollectionChanged(new NotifyCollectionChangedEventArgs(NotifyCollectionChangedAction.Reset));
    }
}
```

---

## 11) Integration checklist for new projects

1. Add ScottPlot.WPF package and `WpfPlot` in XAML.
2. Add model/snapshot/controller/worker classes.
3. Wire ViewModel start/stop with app lifecycle.
4. Connect ingest adapter to your real data source.
5. Bind chart view delegates/properties to ViewModel.
6. Validate interactions (X zoom, Y zoom, pan, follow, scrollbar).
7. Tune constants using `09-tuning-checklist.md`.

---

## 12) Production hardening notes

- Replace silent catches with structured logging.
- Add queue depth alarms and drop counters.
- Add watchdog for worker loop health.
- Add feature flags for decimation profile and target FPS.
- Add unit tests for index mapping and window clamping.

Use these templates as scaffolding, then shape by product requirements.
