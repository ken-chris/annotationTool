# Annotation Selection Feature

## Overview
You can now **click to select** annotations and delete them with a single action.

## How to Use

### Method 1: Click + Button
1. **Click on any annotation region** to select it
   - The annotation will be highlighted (thicker border, more opaque)
   - Status bar shows: "Selected: 'Label' (start - end) | Press Delete key to remove"

2. **Click "Delete Selected Annotation" button**
   - The selected annotation is deleted immediately
   - No confirmation dialog (since you explicitly selected it)

### Method 2: Click + Keyboard Shortcut
1. **Click on any annotation region** to select it
2. **Press the Delete key** (or use Edit menu → Delete Selected Annotation)
   - The annotation is removed immediately

### Visual Feedback
- **Normal annotation**: 2px border, 80/255 alpha transparency
- **Selected annotation**: 4px border, 120/255 alpha transparency (more visible)

### Menu & Shortcuts
- **Edit → Delete Selected Annotation** (Delete key)
- **Edit → Clear All Annotations** (Ctrl+Shift+D)

## Features

✅ **Click to select** - Click any annotation region to select it  
✅ **Visual highlight** - Selected annotations are visually distinct  
✅ **Status bar feedback** - Shows which annotation is selected  
✅ **Keyboard shortcut** - Press Delete key to remove selected annotation  
✅ **Button action** - "Delete Selected Annotation" button for mouse users  
✅ **Menu integration** - Edit menu has delete options  
✅ **No confirmation** - Since you explicitly selected the annotation, no dialog needed  

## Technical Details

### New Signal
- `annotation_selected(Annotation)` - Emitted when annotation is clicked

### New Methods (TimeSeriesWidget)
- `select_annotation(annotation)` - Select and highlight annotation
- `delete_selected_annotation()` - Delete currently selected annotation
- `_update_annotation_appearance(annotation, selected)` - Update visual styling

### New Methods (MainWindow)
- `on_annotation_selected(annotation)` - Handle selection signal
- `delete_selected_annotation()` - Delegate to widget
- `clear_all_annotations()` - Delegate to widget

### Click Handler
Each LinearRegionItem connects its `sigClicked` signal to select the annotation:
```python
region.sigClicked.connect(
    lambda rgn=region, ann=annotation: self.select_annotation(ann)
)
```

## Workflow Comparison

### Old Way (Right-click)
1. Right-click annotation
2. Click "Delete Annotation"
3. Confirm in dialog

### New Way (Click + Delete)
1. Click annotation
2. Press Delete key
✅ **Faster and more intuitive!**

## Notes
- Only one annotation can be selected at a time
- Clicking another annotation deselects the previous one
- Deleting a selected annotation clears the selection
- Creating new annotations doesn't affect selection
