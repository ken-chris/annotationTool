# Annotation Functionality Guide

## Overview

The sensor data annotation tool now includes full annotation functionality, allowing you to label and categorize regions of time series data.

## Features

### 1. **Create Annotations**
- Drag the **blue region selector** on the time series plot to select a time range
- Choose an annotation label from the **Annotation Labels** panel (left side)
- Click **"Create Annotation from Region"** button
- The annotation appears as a colored overlay on all channel plots

### 2. **Manage Annotation Labels**
- **Add Label**: Create new annotation categories with custom names
- **Edit Label**: Rename existing labels
- **Remove Label**: Delete unused labels
- **Change Color**: Pick a custom color for each label
- **Select Label**: Click a label to make it active for new annotations

### 3. **Edit Annotations**
- **Resize**: Drag the edges of annotation regions to adjust time bounds
- **Add Notes**: Right-click an annotation and select "Edit" to add notes
- **Delete**: Right-click and select "Delete Annotation"
- **Sync**: All channels show the same annotations synchronized

### 4. **Overlap Detection**
- The tool warns you when creating overlapping annotations
- You can choose to create them anyway or cancel

### 5. **Export Annotations**
Use **File → Export Annotations** to save your work:
- **JSON format**: Structured data with all annotation details
- **CSV format**: Spreadsheet-compatible for analysis

### 6. **Save/Load Sessions**
- **File → Save Session**: Save annotations with data file reference
- **File → Load Session**: Restore annotations from a previous session

## Workflow Example

1. **Load Data**: File → Open → Select sensor data file
2. **Set Up Labels**:
   - Add labels like "Walking", "Running", "Resting"
   - Assign distinct colors to each
3. **Annotate**:
   - Select "Walking" label
   - Drag region selector to walking period (e.g., 0-5 seconds)
   - Click "Create Annotation from Region"
   - Repeat for other activities
4. **Review**:
   - Switch between Time Series, Spectrogram, and FFT tabs
   - Annotations remain visible across views
5. **Export**:
   - File → Export Annotations → Choose JSON or CSV
   - Use annotations in your analysis pipeline

## Keyboard Shortcuts

- **Ctrl+O**: Open data file
- **Ctrl+S**: Save annotation session
- **Ctrl+E**: Export annotations

## Tips

- **Multi-Channel**: Annotations span all channels - useful for whole-sensor events
- **Visual Distinction**: Use high-contrast colors for easy identification
- **Notes Field**: Add detailed observations for each annotation
- **CSV Export**: Perfect for importing into pandas/Excel for statistical analysis
- **JSON Export**: Preserves all metadata including notes and precise timestamps

## Annotation Data Format

### JSON Export Structure
```json
{
  "annotations": [
    {
      "label": "Walking",
      "start_time": 0.0,
      "end_time": 5.2,
      "duration": 5.2,
      "color": [255, 0, 0],
      "notes": "Normal walking pace"
    }
  ],
  "metadata": {
    "sensor_data_file": "sample_data_3ch.csv",
    "n_annotations": 1,
    "export_timestamp": "2024-01-15T10:30:00"
  }
}
```

### CSV Export Structure
```csv
label,start_time,end_time,duration,notes
Walking,0.0,5.2,5.2,Normal walking pace
Running,5.2,10.5,5.3,Sprint interval
```

## Technical Details

### Implementation
- **Time Series Widget**: Manages annotation regions using PyQtGraph LinearRegionItem
- **Annotation Model**: Dataclass with start/end times, label, color, notes
- **Synchronization**: All channels display the same annotations with matching colors
- **Export Utilities**: JSON and CSV formatters in `src/utils/export.py`

### Annotation Storage
- Annotations stored in memory during session
- Export saves to disk in structured format
- Load session restores annotations from saved file

### Visual Representation
- Each annotation = LinearRegionItem overlay on time series plots
- Semi-transparent fill (80/255 alpha) for visibility
- Colored border (2px width) matches label color
- Movable/resizable with mouse drag

## Troubleshooting

**Annotations not appearing?**
- Ensure data is loaded first (File → Open)
- Check that the time range is visible in the plot
- Try zooming out to see the full timeline

**Can't create annotation?**
- Select an annotation label from the panel first
- Ensure region selector has valid start < end times
- Check for overlap warnings and respond accordingly

**Export failing?**
- Verify you have write permissions in the target directory
- Ensure filename has correct extension (.json or .csv)
- Check that annotations exist (at least one created)

## Future Enhancements
- [ ] Batch annotation from CSV template
- [ ] Annotation validation rules
- [ ] Auto-annotation using ML models
- [ ] Collaborative annotation (multi-user)
- [ ] Annotation statistics dashboard
