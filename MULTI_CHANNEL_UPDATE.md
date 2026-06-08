# Multi-Channel Layout Update

## Changes Made

### ✅ Time Series Widget
- **Separate plot for each channel** - Each channel gets its own PlotWidget with independent y-axis
- **Scrollable container** - QScrollArea with vertical scrollbar for many channels
- **Synchronized region selectors** - Region selection appears on all plots and stays in sync
- **Linked x-axes** - Pan and zoom affects all channels together
- **Clean layout** - Only bottom plot shows x-axis labels

### ✅ FFT Widget
- **Separate plot for each channel** - Each channel's FFT displayed in its own plot
- **Scrollable container** - Vertical scrollbar for many channels
- **Per-channel peak detection** - Peak frequencies shown for each channel separately
- **Linked x-axes** - Frequency axes zoom together
- **Info labels** - Each channel shows its top peak frequencies below the plot

### ✅ Spectrogram Widget
- **Separate spectrogram for each channel** - Each channel's STFT in its own heatmap
- **Scrollable container** - Vertical scrollbar for many channels
- **Independent color bars** - Each plot can have its own intensity scale
- **Linked x-axes** - Time axes zoom together
- **Per-channel computation** - STFT computed independently for each channel

## Layout Structure

```
All Tabs:
┌─────────────────────────────────────┐
│ ┌─────────────────────────────────┐ │
│ │ Channel 1 Plot                  │ │
│ │ [Peak info / Color bar]         │ │
│ ├─────────────────────────────────┤ │ ← Scrollable
│ │ Channel 2 Plot                  │ │    Area
│ │ [Peak info / Color bar]         │ │
│ ├─────────────────────────────────┤ │
│ │ Channel 3 Plot                  │ │
│ │ [Peak info / Color bar]         │ │
│ └─────────────────────────────────┘ │
│ [Overall Info / Controls]           │ ← Fixed at bottom
└─────────────────────────────────────┘
```

## Benefits

1. **Better visibility** - Each channel has dedicated space, no overlapping signals
2. **Independent y-scales** - Each channel can have its own amplitude/frequency range
3. **Easier comparison** - Stacked plots make it easy to compare timing across channels
4. **Scalable** - Handles any number of channels with automatic scrollbar
5. **Consistent UX** - All three tabs use the same multi-plot layout

## Technical Details

### Fixed Height Plots
- Each plot: 150-300px height
- Prevents tiny plots when many channels
- Consistent viewing experience

### Synchronized Interactions
- **Time Series**: Region selectors sync across all channel plots
- **FFT**: X-axes (frequency) linked for synchronized zoom
- **Spectrogram**: X-axes (time) linked for synchronized zoom

### Memory Efficiency
- PyQtGraph auto-downsampling still active
- Each plot independently optimized
- No redundant data storage

## Usage Tips

1. **Scroll** to view all channels when you have many
2. **Zoom** on any plot - linked axes keep everything aligned
3. **Region selection** (Time Series) - drag on any channel plot
4. **Peak info** (FFT) - Check below each channel's plot for top frequencies
5. **Color intensity** (Spectrogram) - Each channel's color scale auto-adjusts

## Example with 3-Channel Data

**Before**: Single plot with 3 overlapping lines (hard to distinguish)
**After**: 3 separate plots stacked vertically (crystal clear)

- Channel 1 (Red): 10 Hz base + harmonics
- Channel 2 (Green): 15 Hz base + harmonics  
- Channel 3 (Blue): 20 Hz base + harmonics

Each clearly visible in its own plot with appropriate scaling!
