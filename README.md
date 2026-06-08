# Sensor Data Annotation Tool

A high-performance desktop application for annotating time series sensor data with real-time FFT and STFT visualization.

## Features

- 🚀 **High-performance visualization** - Handle millions of data points with OpenGL acceleration
- 📊 **Time series viewer** - Multi-channel sensor data with pan/zoom
- 🌈 **STFT Spectrogram** - Configurable window size, overlap, and color maps
- 📈 **FFT Analysis** - Frequency domain analysis of user-selected regions
- 🏷️ **Annotation system** - Drag-and-drop region annotation with custom labels
- 💾 **Export** - Save annotations to JSON/CSV formats

## Installation

### Prerequisites
- Python 3.10 or higher
- pip (Python package manager)

### Setup

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

**Note:** On Windows, you can simply double-click `run.bat` which will automatically install dependencies and launch the application.

3. Run the application:
```bash
# From project root directory:
python src/main.py

# Or on Windows:
run.bat
```

## Usage

### Loading Data
- **File > Open** or `Ctrl+O` to load sensor data
- Supported formats: CSV, NumPy (.npy), HDF5 (.h5)

### Viewing Data
- **Time Series Tab**: Pan (drag), zoom (scroll), select regions (drag the linear region selector)
- **Spectrogram Tab**: View STFT heatmap with configurable parameters
- **FFT Tab**: View frequency domain of selected region

### Annotating
1. Define annotation labels in the Annotation Panel
2. Select a label
3. Drag to create annotation regions on the time series
4. Right-click regions to edit/delete

### Exporting
- **File > Export Annotations** or `Ctrl+E` to save annotations

## Data Format

### CSV Format
```
timestamp,channel1,channel2,channel3
0.0,0.5,0.3,0.1
0.001,0.6,0.4,0.2
...
```

### NumPy Format
- 2D array: shape `(n_samples, n_channels+1)` where first column is timestamp

### HDF5 Format
- Dataset `data`: 2D array with shape `(n_samples, n_channels+1)`
- Attribute `sample_rate` (optional)

## Keyboard Shortcuts

- `Ctrl+O`: Open file
- `Ctrl+S`: Save annotations
- `Ctrl+E`: Export annotations
- `Ctrl+Q`: Quit

## Building Standalone Executable

```bash
pyinstaller --onefile --windowed --name SensorAnnotationTool src/main.py
```

## License

MIT License

## Author

Created with PyQt6 and PyQtGraph
