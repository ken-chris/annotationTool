"""
Getting Started Guide - Quick start instructions for the Sensor Data Annotation Tool
"""

# Getting Started

## Installation

1. **Install Python 3.10 or higher** if not already installed
   - Download from https://www.python.org/
   - Make sure to check "Add Python to PATH" during installation

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   
   Or on Windows, simply double-click **`run.bat`** which will handle everything automatically!

3. **Generate sample data** (optional, for testing):
   ```bash
   python generate_sample_data.py
   ```

4. **Run the application:**
   ```bash
   python src/main.py
   ```
   
   Or on Windows: **double-click `run.bat`**

## Quick Start Guide

### 1. Load Data
- Click **File > Open** (or press `Ctrl+O`)
- Select a data file (CSV, NumPy `.npy`, or HDF5 `.h5`)
- Sample data is available in `sample_data/` if you ran the generator

### 2. Explore Time Series
- **Time Series tab** shows your sensor data
- **Pan**: Click and drag on the plot
- **Zoom**: Scroll wheel
- **Select region**: Drag the shaded region selector

### 3. View FFT
- Switch to the **FFT tab**
- Drag the region selector on the Time Series tab to update the FFT
- Or enter precise start/end times in the input fields
- Peak frequencies are displayed below the plot

### 4. View Spectrogram
- Switch to the **Spectrogram tab**
- Adjust parameters in the left panel:
  - **Window Size**: FFT window size (64-8192 samples)
  - **Overlap**: Window overlap percentage (0-90%)
  - **Window Type**: hann, hamming, blackman, or bartlett
- Click **Apply STFT Parameters** to update

### 5. Annotate Data (Coming Soon)
- Define annotation labels in the **Annotation Labels** panel
- Select a label (it becomes highlighted)
- Drag to create annotation regions on the Time Series plot
- Right-click regions to edit or delete
- Change label colors with the **Change Color** button

### 6. Export Annotations
- Click **File > Export Annotations** (or press `Ctrl+E`)
- Choose JSON or CSV format
- Annotations include: label, start/end times, duration, color, notes

## Data Format Requirements

### CSV Format
```
timestamp,channel1,channel2,channel3
0.0,0.5,0.3,0.1
0.001,0.6,0.4,0.2
0.002,0.7,0.5,0.3
...
```

### NumPy Format
- 2D array with shape `(n_samples, n_channels+1)`
- First column: timestamps
- Remaining columns: sensor channels

### HDF5 Format
- Dataset named `data` (or specify custom name)
- 2D array with shape `(n_samples, n_channels+1)`
- Optional attributes: `sample_rate`, `channel_names`

## Tips and Tricks

1. **Performance**: PyQtGraph automatically downsamples large datasets for smooth rendering
2. **Multiple channels**: All channels are plotted with different colors
3. **Keyboard shortcuts**:
   - `Ctrl+O`: Open file
   - `Ctrl+S`: Save annotations
   - `Ctrl+E`: Export annotations
   - `Ctrl+Q`: Quit
4. **STFT resolution**: Increase window size for better frequency resolution, increase overlap for better time resolution

## Troubleshooting

**Problem**: Application doesn't start
- **Solution**: Make sure all dependencies are installed: `pip install -r requirements.txt`

**Problem**: File won't load
- **Solution**: Check the data format requirements above
- **Solution**: Look at the error message for specific details

**Problem**: Plots are slow or laggy
- **Solution**: PyQtGraph should handle millions of points efficiently with OpenGL acceleration
- **Solution**: If still slow, try reducing the data size or check GPU drivers

**Problem**: STFT computation is slow
- **Solution**: Use smaller window sizes (256 or 512)
- **Solution**: The computation happens when you switch to the Spectrogram tab or change parameters

## Next Steps

- Create your own sensor data files in the supported formats
- Define custom annotation labels for your use case
- Export annotations for further analysis or machine learning
- Consider building a standalone executable with PyInstaller (see README.md)

## Need Help?

Check the main README.md for more detailed information about features and implementation details.
