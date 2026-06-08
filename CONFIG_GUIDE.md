# Configuration File Guide

## Overview
The annotation tool now supports loading configuration files that set default parameters for:
- Annotation labels and colors
- STFT (spectrogram) parameters
- DB transform settings
- UI preferences

## Usage

### Loading a Config
1. **Menu**: File → Load Config... (Ctrl+Shift+O)
2. Select your JSON config file
3. All settings will be applied immediately

### Saving Current Config
1. **Menu**: File → Save Config As... (Ctrl+Shift+S)
2. Choose a location and filename
3. Your current settings will be saved as JSON

### Example Config File (`config_example.json`)

```json
{
  "labels": [
    {
      "name": "Walking",
      "color": [255, 0, 0]
    },
    {
      "name": "Running",
      "color": [0, 255, 0]
    },
    {
      "name": "Standing",
      "color": [0, 0, 255]
    }
  ],
  "stft": {
    "window_size": 256,
    "overlap": 0.5,
    "window_type": "hann",
    "use_db": true,
    "db_ref": 1e-10,
    "vmin": -80,
    "vmax": 0
  },
  "fft": {
    "nperseg": 256,
    "window": "hann"
  },
  "ui": {
    "plot_height_min": 200,
    "plot_height_max": 250
  },
  "data": {
    "default_sample_rate": 100
  }
}
```

## Configuration Parameters

### Labels
- **name**: Label text (e.g., "Walking", "Running")
- **color**: RGB tuple [R, G, B] where values are 0-255

### STFT Parameters
- **window_size**: FFT window size in samples (64-8192)
- **overlap**: Window overlap as fraction (0.0-0.9)
- **window_type**: Window function ("hann", "hamming", "blackman", "bartlett")
- **use_db**: Convert magnitude to decibels (true/false)
- **db_ref**: Reference value for dB conversion (typically 1e-10)
- **vmin**: Minimum value for colormap (dB)
- **vmax**: Maximum value for colormap (dB)

### FFT Parameters
- **nperseg**: Samples per segment
- **window**: Window function type

### UI Parameters
- **plot_height_min**: Minimum plot height in pixels
- **plot_height_max**: Maximum plot height in pixels

### Data Parameters
- **default_sample_rate**: Default sampling rate in Hz

## Tips

- **Start from template**: Copy `config_example.json` and modify it
- **Share configs**: Use config files to standardize annotation settings across team
- **Different datasets**: Create separate configs for different data types
- **Quick switching**: Keep multiple config files for different annotation scenarios

## Workflow Example

1. Load your sensor data
2. Load appropriate config for that data type
3. All labels, colors, and STFT settings are applied automatically
4. Start annotating with consistent settings
5. Modify settings as needed during annotation
6. Save updated config for future use
