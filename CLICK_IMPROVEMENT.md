# Annotation Click Detection Improvements

## Overview
Enhanced the `AnnotationRegion` class to provide reliable click detection that distinguishes between clicks and drags, preventing intermittent selection and deletion issues.

## Problem
The original implementation had two main issues:
1. **Click vs Drag Confusion**: Mouse events with even tiny movements were interpreted as drags, preventing clicks from registering
2. **Double-Click Events**: Rapid clicks could fire multiple times, causing toggle behavior to flip back and forth unintentionally

## Solution
Implemented a three-part approach combining:
1. **Mouse Release with Distance Threshold** (Option 1)
2. **Debouncing** (Option 2)  
3. **Hover Visual Feedback** (Option 4)

## Implementation Details

### 1. Mouse Release with Distance Threshold
- **Press**: Records mouse position in `mousePressEvent()`
- **Release**: Calculates distance moved in `mouseReleaseEvent()`
- **Click Detection**: Only emits `clicked` signal if movement < 5 pixels
- **Benefits**: 
  - Tolerates small mouse jitter/tremor
  - Doesn't interfere with drag operations
  - Standard GUI interaction pattern

### 2. Debouncing
- Tracks timestamp of last click
- Requires 200ms gap between successive clicks
- Prevents double-event processing from firing multiple toggles
- **Benefits**:
  - Eliminates accidental rapid-click issues
  - Works on all input devices (mouse, trackpad, touchscreen)

### 3. Hover Visual Feedback
- Increases annotation opacity by +40 alpha on hover
- Provides immediate visual confirmation of clickable target
- Restores original appearance on hover leave
- **Benefits**:
  - User knows annotation is interactive
  - Improves discoverability
  - Better perceived responsiveness

## Code Changes

### `AnnotationRegion` Class (src/widgets/timeseries_widget.py)

```python
class AnnotationRegion(pg.LinearRegionItem):
    """
    Custom LinearRegionItem with reliable click detection.
    Uses mouse release with distance threshold and debouncing to distinguish clicks from drags.
    Includes hover visual feedback.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAcceptHoverEvents(True)
        
        # Click detection
        self.mouse_press_pos = None
        self.click_threshold = 5  # pixels
        
        # Debouncing
        self.last_click_time = 0
        self.click_debounce_ms = 200  # milliseconds
        
        # Hover effect
        self.base_brush = None
    
    def mouseReleaseEvent(self, event):
        """Emit clicked only if mouse didn't move much (not a drag)."""
        if event.button() == Qt.MouseButton.LeftButton and self.mouse_press_pos:
            distance = (event.pos() - self.mouse_press_pos).manhattanLength()
            
            if distance < self.click_threshold:
                current_time = QDateTime.currentMSecsSinceEpoch()
                if current_time - self.last_click_time > self.click_debounce_ms:
                    self.clicked.emit()
                    self.last_click_time = current_time
            
            self.mouse_press_pos = None
        super().mouseReleaseEvent(event)
    
    def hoverEnterEvent(self, event):
        """Increase opacity on hover for visual feedback."""
        # Increases alpha by +40, capped at 255
    
    def hoverLeaveEvent(self, event):
        """Restore original opacity when hover ends."""
```

### `_update_annotation_appearance` Enhancement
Updated to maintain `base_brush` for proper hover effect:
```python
region.setBrush(brush)
region.base_brush = brush  # Store for hover to work correctly
```

## Configuration Parameters

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `click_threshold` | 5 pixels | Maximum movement to count as click (not drag) |
| `click_debounce_ms` | 200 ms | Minimum time between successive clicks |
| `hover_alpha_increase` | +40 | Alpha boost on hover for visibility |

## User Experience Improvements

### Before:
- ❌ Clicks with tiny mouse movement = drag = no selection
- ❌ Rapid clicks = double toggle = appears broken
- ❌ No visual feedback before clicking
- ❌ Delete sometimes didn't work
- ❌ Selection appeared inconsistent

### After:
- ✅ Tolerates natural mouse movement (up to 5px)
- ✅ Debouncing prevents double-toggle issues
- ✅ Hover provides immediate visual confirmation
- ✅ Reliable click detection every time
- ✅ Drag still works perfectly for resizing annotations

## Testing Notes

Test the following scenarios:
1. **Click-and-hold-still**: Should select annotation
2. **Click-with-small-movement** (< 5px): Should select annotation  
3. **Drag** (> 5px movement): Should resize annotation, NOT select
4. **Rapid double-click**: Should toggle once (debounced)
5. **Hover**: Should see opacity increase
6. **Delete selected**: Should work reliably now

## Alternative Approaches Considered

- **Modifier Key Selection** (Ctrl+Click): 100% reliable but less intuitive
- **Double-Click Selection**: Less discoverable
- **Context Menu Only**: Slower workflow
- **Mouse Press (original)**: Fast but unreliable

The implemented solution provides the best balance of reliability and user experience.
