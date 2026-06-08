"""
Time series viewer widget using PyQtGraph.
"""
import pyqtgraph as pg
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QScrollArea, QMenu, QInputDialog, QMessageBox, QComboBox
)
from PyQt6.QtCore import pyqtSignal, Qt, QEvent, QDateTime, QThread
from PyQt6.QtGui import QAction
from typing import Optional, List, Dict
import numpy as np
import threading
from src.models.sensor_data import SensorData
from src.models.annotation import Annotation


class AnnotationRegion(pg.LinearRegionItem):
    """
    Custom LinearRegionItem with reliable click detection.
    Works around PyQtGraph's mouse capture during drag by using mouseClickEvent.
    Includes hover visual feedback and debouncing.
    """
    
    clicked = pyqtSignal()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAcceptHoverEvents(True)
        
        # Debouncing
        self.last_click_time = 0
        self.click_debounce_ms = 200  # milliseconds between clicks
        
        # Store original brush for hover effect
        self.base_brush = None
    
    def mouseClickEvent(self, event):
        """
        Handle click events. This is called by PyQtGraph when a click is detected
        (press + release without significant movement).
        """
        if event.button() == Qt.MouseButton.LeftButton:
            # Check debounce time
            current_time = QDateTime.currentMSecsSinceEpoch()
            time_since_last = current_time - self.last_click_time
            
            if time_since_last > self.click_debounce_ms:
                self.clicked.emit()
                self.last_click_time = current_time
                event.accept()  # Mark as handled
        else:
            # Let parent handle non-left clicks
            super().mouseClickEvent(event)
    
    def hoverEnterEvent(self, event):
        """Increase opacity on hover for visual feedback."""
        if not self.base_brush:
            # Store the current brush (it's a property, not a method)
            self.base_brush = self.brush
        
        # Create hover brush with increased alpha
        current_brush = self.brush
        hover_brush = pg.mkBrush(current_brush.color())
        current_alpha = current_brush.color().alpha()
        # Increase alpha by 40, capped at 255
        hover_alpha = min(current_alpha + 40, 255)
        color = hover_brush.color()
        color.setAlpha(hover_alpha)
        hover_brush.setColor(color)
        self.setBrush(hover_brush)
        
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """Restore original opacity when hover ends."""
        if self.base_brush:
            self.setBrush(self.base_brush)
        super().hoverLeaveEvent(event)


class TimeSeriesWidget(QWidget):
    """
    Widget for displaying time series data with interactive region selection.
    Each channel is displayed in a separate plot window.
    """
    
    # Signal emitted when region selection changes
    region_changed = pyqtSignal(float, float)  # start_time, end_time
    
    # Signal emitted when annotations change
    annotations_changed = pyqtSignal()
    
    # Signal emitted when an annotation is selected
    annotation_selected = pyqtSignal(object)  # Annotation object or None
    
    # Signal emitted when the view range changes (pan/zoom)
    view_range_changed = pyqtSignal(float, float)  # x_min, x_max
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.sensor_data: Optional[SensorData] = None
        self.region_item: Optional[pg.LinearRegionItem] = None
        self.plot_widgets: List[pg.PlotWidget] = []
        self.plot_items: List[pg.PlotDataItem] = []
        self.region_items: List[pg.LinearRegionItem] = []
        
        # Annotation management
        self.annotations: List[Annotation] = []
        self.annotation_regions: Dict[Annotation, List[pg.LinearRegionItem]] = {}
        self.active_label: str = "Label1"
        self.active_color: tuple = (255, 0, 0)
        self.selected_annotation: Optional[Annotation] = None
        
        # Audio playback state
        self.is_playing: bool = False
        self.play_button: Optional[QPushButton] = None
        self.stop_button: Optional[QPushButton] = None
        self.channel_combo: Optional[QComboBox] = None
        
        # Flag to prevent signal recursion
        self.is_updating_range = False
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create scroll area for plots
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Container widget for plots
        self.plots_container = QWidget()
        self.plots_layout = QVBoxLayout(self.plots_container)
        self.plots_layout.setSpacing(2)
        self.plots_layout.setContentsMargins(0, 0, 0, 0)
        
        self.scroll_area.setWidget(self.plots_container)
        main_layout.addWidget(self.scroll_area)
        
        # Region selection controls
        controls_layout = QHBoxLayout()
        
        controls_layout.addWidget(QLabel("Region:"))
        
        self.start_edit = QLineEdit()
        self.start_edit.setPlaceholderText("Start (s)")
        self.start_edit.setMaximumWidth(100)
        self.start_edit.returnPressed.connect(self.update_region_from_inputs)
        controls_layout.addWidget(self.start_edit)
        
        controls_layout.addWidget(QLabel("to"))
        
        self.end_edit = QLineEdit()
        self.end_edit.setPlaceholderText("End (s)")
        self.end_edit.setMaximumWidth(100)
        self.end_edit.returnPressed.connect(self.update_region_from_inputs)
        controls_layout.addWidget(self.end_edit)
        
        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self.update_region_from_inputs)
        controls_layout.addWidget(apply_btn)
        
        # Home selection button
        home_selection_btn = QPushButton("Home Selection")
        home_selection_btn.clicked.connect(self.home_selection)
        home_selection_btn.setToolTip("Move selection to 10%-30% of currently visible segment")
        home_selection_btn.setMaximumWidth(140)
        controls_layout.addWidget(home_selection_btn)
        
        # Channel selection dropdown for playback
        controls_layout.addWidget(QLabel("Play Channel:"))
        self.channel_combo = QComboBox()
        self.channel_combo.setToolTip("Select which channel to play")
        self.channel_combo.setMaximumWidth(120)
        controls_layout.addWidget(self.channel_combo)
        
        # Play segment button
        self.play_button = QPushButton("▶ Play Segment")
        self.play_button.clicked.connect(self.play_selected_segment)
        self.play_button.setToolTip("Play the highlighted region as audio")
        self.play_button.setMaximumWidth(140)
        controls_layout.addWidget(self.play_button)
        
        # Stop playback button
        self.stop_button = QPushButton("⏹ Stop Playback")
        self.stop_button.clicked.connect(self.stop_playback)
        self.stop_button.setToolTip("Stop audio playback")
        self.stop_button.setMaximumWidth(140)
        self.stop_button.setEnabled(False)  # Disabled until playback starts
        controls_layout.addWidget(self.stop_button)
        
        controls_layout.addStretch()
        
        # Annotation controls
        create_annotation_btn = QPushButton("Create Annotation from Region")
        create_annotation_btn.clicked.connect(self.create_annotation_from_region)
        controls_layout.addWidget(create_annotation_btn)
        
        delete_selected_btn = QPushButton("Delete Selected Annotation")
        delete_selected_btn.clicked.connect(self.delete_selected_annotation)
        delete_selected_btn.setToolTip("Click an annotation to select it, then click this button to delete")
        controls_layout.addWidget(delete_selected_btn)
        
        clear_annotations_btn = QPushButton("Clear All Annotations")
        clear_annotations_btn.clicked.connect(self.clear_all_annotations)
        controls_layout.addWidget(clear_annotations_btn)
        
        main_layout.addLayout(controls_layout)
    
    def set_data(self, sensor_data: SensorData):
        """
        Load and display sensor data.
        
        Args:
            sensor_data: SensorData object to display
        """
        self.sensor_data = sensor_data
        
        # Clear existing plots
        self.clear_plots()
        
        # Create a plot for each channel
        for i in range(sensor_data.n_channels):
            channel_data = sensor_data.get_channel(i)
            
            # Create plot widget
            plot_widget = pg.PlotWidget()
            plot_widget.setBackground('w')
            plot_widget.showGrid(x=True, y=True, alpha=0.3)
            plot_widget.setLabel('left', sensor_data.channel_names[i])
            
            # Only show x-axis label on last plot
            if i == sensor_data.n_channels - 1:
                plot_widget.setLabel('bottom', 'Time', units='s')
            else:
                plot_widget.getAxis('bottom').setStyle(showValues=False)
            
            # Set fixed height for each plot
            plot_widget.setMinimumHeight(200)
            plot_widget.setMaximumHeight(400)
            
            # Enable anti-aliasing
            plot_widget.setAntialiasing(True)
            
            # Plot data with black color for all channels
            plot_item = plot_widget.plot(
                sensor_data.timestamps,
                channel_data,
                pen=pg.mkPen(color='k', width=1)
            )
            
            # Add region selector to each plot
            region_item = pg.LinearRegionItem(
                brush=pg.mkBrush(100, 100, 200, 50),
                movable=True
            )
            
            # Set higher z-value so it's drawn on top of annotations
            region_item.setZValue(1000)
            
            # Connect to sync function
            region_item.sigRegionChanged.connect(
                lambda item=region_item: self.on_region_changed_internal(item)
            )
            
            plot_widget.addItem(region_item)
            
            # Store references
            self.plot_widgets.append(plot_widget)
            self.plot_items.append(plot_item)
            self.region_items.append(region_item)
            
            # Add to layout
            self.plots_layout.addWidget(plot_widget)
        
        # Link x-axes of all plots so they pan/zoom together
        if len(self.plot_widgets) > 1:
            for i in range(1, len(self.plot_widgets)):
                self.plot_widgets[i].setXLink(self.plot_widgets[0])
        
        # Connect to view range changes on the first plot
        if self.plot_widgets:
            view_box = self.plot_widgets[0].getViewBox()
            view_box.sigRangeChanged.connect(self.on_view_range_changed)
        
        # Initialize region position
        self.initialize_region()
        
        # Auto-range to fit data
        for plot_widget in self.plot_widgets:
            plot_widget.autoRange()
        
        # Populate channel dropdown for playback selection
        if self.channel_combo is not None:
            self.channel_combo.clear()
            if hasattr(sensor_data, 'channel_names') and sensor_data.channel_names:
                for i, channel_name in enumerate(sensor_data.channel_names):
                    self.channel_combo.addItem(f"Channel {i}: {channel_name}", i)
            else:
                # Fallback: create generic channel names based on n_channels
                for i in range(sensor_data.n_channels):
                    self.channel_combo.addItem(f"Channel {i}", i)
            # Set first channel as default
            if self.channel_combo.count() > 0:
                self.channel_combo.setCurrentIndex(0)
    
    def clear_plots(self):
        """Clear all existing plots."""
        # Remove all widgets from layout
        while self.plots_layout.count():
            item = self.plots_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Clear lists
        self.plot_widgets.clear()
        self.plot_items.clear()
        self.region_items.clear()
    
    def initialize_region(self):
        """Initialize region selector position."""
        if self.sensor_data is None or not self.region_items:
            return
        
        # Set initial position at 10-20% of data range
        duration = self.sensor_data.duration
        start = self.sensor_data.timestamps[0] + duration * 0.1
        end = self.sensor_data.timestamps[0] + duration * 0.2
        
        # Set all regions to same position
        for region_item in self.region_items:
            region_item.setRegion([start, end])
        
        # Update input fields
        self.update_inputs_from_region()
    
    def on_region_changed_internal(self, changed_item: pg.LinearRegionItem):
        """
        Handle region change event and sync all regions.
        
        Args:
            changed_item: The region item that was changed
        """
        if not self.region_items:
            return
        
        start, end = changed_item.getRegion()
        
        # Sync all other regions (block signals to prevent recursion)
        for region_item in self.region_items:
            if region_item != changed_item:
                region_item.blockSignals(True)
                region_item.setRegion([start, end])
                region_item.blockSignals(False)
        
        # Update input fields
        self.start_edit.setText(f"{start:.3f}")
        self.end_edit.setText(f"{end:.3f}")
        
        # Emit signal
        self.region_changed.emit(start, end)
    
    def on_view_range_changed(self):
        """Handle view range changes (pan/zoom) and emit signal."""
        if self.is_updating_range or not self.plot_widgets:
            return
        
        # Get the current x-axis range from the first plot
        view_box = self.plot_widgets[0].getViewBox()
        x_range = view_box.viewRange()[0]  # Returns [[xmin, xmax], [ymin, ymax]]
        
        # Emit signal with the new range
        self.view_range_changed.emit(x_range[0], x_range[1])
    
    def update_inputs_from_region(self):
        """Update input fields from current region."""
        if not self.region_items:
            return
        
        start, end = self.region_items[0].getRegion()
        self.start_edit.setText(f"{start:.3f}")
        self.end_edit.setText(f"{end:.3f}")
    
    def update_region_from_inputs(self):
        """Update region from input field values."""
        if not self.region_items:
            return
        
        try:
            start = float(self.start_edit.text())
            end = float(self.end_edit.text())
            
            if start >= end:
                return
            
            # Update all regions
            for region_item in self.region_items:
                region_item.setRegion([start, end])
            
        except ValueError:
            # Invalid input, reset to current region
            self.update_inputs_from_region()
    
    def home_selection(self):
        """Move the blue selection to 10%-30% of the currently visible segment."""
        if not self.plot_widgets or not self.region_items:
            return
        
        # Get the current visible x-axis range from the first plot
        view_box = self.plot_widgets[0].getViewBox()
        x_range = view_box.viewRange()[0]  # Returns [xmin, xmax]
        x_min, x_max = x_range[0], x_range[1]
        
        # Calculate segment size and position from 10%-30% of the visible segment
        segment_size = x_max - x_min
        start = x_min + segment_size * 0.1
        end = x_min + segment_size * 0.3
        
        # Update all regions
        for region_item in self.region_items:
            region_item.setRegion([start, end])
        
        # Update input fields
        self.update_inputs_from_region()
    
    def get_selected_region(self):
        """
        Get the currently selected time region.
        
        Returns:
            Tuple of (start_time, end_time) or None if no region selected
        """
        if not self.region_items:
            return None
        
        return self.region_items[0].getRegion()
    
    def get_selected_data(self):
        """
        Get the sensor data within the selected region.
        
        Returns:
            Tuple of (timestamps, data) for the selected region
        """
        if self.sensor_data is None or not self.region_items:
            return None, None
        
        start, end = self.region_items[0].getRegion()
        return self.sensor_data.get_time_slice(start, end)
    
    def set_active_label(self, label: str, color: tuple):
        """
        Set the active annotation label and color.
        
        Args:
            label: Label name
            color: RGB color tuple
        """
        self.active_label = label
        self.active_color = color
    
    def create_annotation_from_region(self):
        """Create an annotation from the current region selection."""
        if not self.region_items or self.sensor_data is None:
            QMessageBox.warning(self, "No Data", "Please load data first.")
            return
        
        # Get region bounds
        start, end = self.region_items[0].getRegion()
        
        # Check for overlap with existing annotations
        for existing_annotation in self.annotations:
            if not (end < existing_annotation.start_time or start > existing_annotation.end_time):
                reply = QMessageBox.question(
                    self,
                    "Overlapping Annotation",
                    f"This region overlaps with existing annotation '{existing_annotation.label}' "
                    f"({existing_annotation.start_time:.2f}s - {existing_annotation.end_time:.2f}s).\n\n"
                    "Create annotation anyway?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return
                break
        
        # Create annotation
        annotation = Annotation(
            label=self.active_label,
            start_time=start,
            end_time=end,
            color=self.active_color,
            notes="",
            sample_rate=self.sensor_data.sample_rate if self.sensor_data else None
        )
        
        # Add to list
        self.annotations.append(annotation)
        
        # Create visual regions for each plot
        self.add_annotation_to_plots(annotation)
        
        # Emit signal
        self.annotations_changed.emit()

    
    def add_annotation_to_plots(self, annotation: Annotation):
        """
        Add visual representation of annotation to all plots.
        
        Args:
            annotation: Annotation object to visualize
        """
        region_items = []
        
        for plot_widget in self.plot_widgets:
            # Create custom LinearRegionItem with annotation color
            r, g, b = annotation.color
            region = AnnotationRegion(
                values=[annotation.start_time, annotation.end_time],
                brush=pg.mkBrush(r, g, b, 60),  # Start with lighter alpha
                pen=pg.mkPen(color=(r, g, b), width=2),
                movable=True
            )
            
            # Connect to update handler
            region.sigRegionChanged.connect(
                lambda rgn=region, ann=annotation: self.on_annotation_region_changed(ann, rgn)
            )
            
            # Connect to click handler for selection
            region.clicked.connect(
                lambda ann=annotation: self.select_annotation(ann)
            )
            
            plot_widget.addItem(region)
            region_items.append(region)
        
        # Store references
        self.annotation_regions[annotation] = region_items
    
    def on_annotation_region_changed(self, annotation: Annotation, region: pg.LinearRegionItem):
        """
        Handle changes to annotation region (drag to resize).
        
        Args:
            annotation: The annotation being modified
            region: The LinearRegionItem that was changed
        """
        start, end = region.getRegion()
        
        # Update annotation data
        annotation.start_time = start
        annotation.end_time = end
        
        # Sync all regions for this annotation
        if annotation in self.annotation_regions:
            for other_region in self.annotation_regions[annotation]:
                if other_region != region:
                    other_region.blockSignals(True)
                    other_region.setRegion([start, end])
                    other_region.blockSignals(False)
        
        # Emit change signal
        self.annotations_changed.emit()
    
    def select_annotation(self, annotation: Annotation):
        """
        Select or deselect an annotation (toggle) and highlight it visually.
        
        Args:
            annotation: Annotation to select/deselect
        """
        # Toggle: if clicking the same annotation, deselect it
        if self.selected_annotation == annotation:
            # Deselect
            self._update_annotation_appearance(annotation, selected=False)
            self.selected_annotation = None
            self.annotation_selected.emit(None)

        else:
            # Deselect previous annotation
            if self.selected_annotation and self.selected_annotation in self.annotation_regions:
                self._update_annotation_appearance(self.selected_annotation, selected=False)
            
            # Select new annotation
            self.selected_annotation = annotation
            self._update_annotation_appearance(annotation, selected=True)
            
            # Emit signal
            self.annotation_selected.emit(annotation)

    
    def _update_annotation_appearance(self, annotation: Annotation, selected: bool):
        """
        Update the visual appearance of an annotation based on selection state.
        
        Args:
            annotation: Annotation to update
            selected: Whether the annotation is selected
        """
        if annotation not in self.annotation_regions:
            return
        
        r, g, b = annotation.color
        
        if selected:
            # Highlight: thicker pen, much more opaque for clear visibility
            pen = pg.mkPen(color=(r, g, b), width=5)
            brush = pg.mkBrush(r, g, b, 180)  # Much more opaque
        else:
            # Normal: standard pen and brush
            pen = pg.mkPen(color=(r, g, b), width=2)
            brush = pg.mkBrush(r, g, b, 60)  # Lighter than before for better contrast
        
        # Update all regions for this annotation
        for region in self.annotation_regions[annotation]:
            # Update the lines (borders)
            for line in region.lines:
                line.setPen(pen)
            # Update the fill brush
            region.setBrush(brush)
            # Update base_brush so hover effect works correctly
            region.base_brush = brush
    
    def delete_selected_annotation(self):
        """Delete the currently selected annotation."""
        if not self.selected_annotation:
            QMessageBox.information(
                self,
                "No Selection",
                "Please click an annotation to select it first."
            )
            return
        
        annotation = self.selected_annotation
        self.selected_annotation = None
        self.delete_annotation(annotation)
    
    def delete_annotation(self, annotation: Annotation):
        """
        Delete an annotation.
        
        Args:
            annotation: Annotation to delete
        """
        # Remove visual regions from all plots
        if annotation in self.annotation_regions:
            regions_to_remove = self.annotation_regions[annotation]
            for i, plot_widget in enumerate(self.plot_widgets):
                if i < len(regions_to_remove):
                    region = regions_to_remove[i]
                    plot_widget.removeItem(region)
            # Remove from dictionary
            del self.annotation_regions[annotation]
        
        # Remove from list
        if annotation in self.annotations:
            self.annotations.remove(annotation)
        
        # Clear selection if this was selected
        if self.selected_annotation == annotation:
            self.selected_annotation = None
            self.annotation_selected.emit(None)
        
        # Emit signal
        self.annotations_changed.emit()
        
        # Update status bar
        status_bar = self.statusBar()
        if status_bar:
            status_bar.showMessage(f"Deleted annotation '{annotation.label}'", 3000)
    
    def clear_all_annotations(self):
        """Clear all annotations."""
        if not self.annotations:
            QMessageBox.information(self, "No Annotations", "No annotations to clear.")
            return
        
        reply = QMessageBox.question(
            self,
            "Clear All Annotations",
            f"Delete all {len(self.annotations)} annotations?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Remove all visual regions from plots
            for annotation in list(self.annotations):
                if annotation in self.annotation_regions:
                    regions_to_remove = self.annotation_regions[annotation]
                    for i, plot_widget in enumerate(self.plot_widgets):
                        if i < len(regions_to_remove):
                            region = regions_to_remove[i]
                            plot_widget.removeItem(region)
            
            # Clear storage
            self.annotations.clear()
            self.annotation_regions.clear()
            self.selected_annotation = None
            
            # Emit signal
            self.annotation_selected.emit(None)
            self.annotations_changed.emit()
            
            # Update status bar
            status_bar = self.statusBar()
            if status_bar:
                status_bar.showMessage("All annotations cleared", 3000)
    
    def get_annotations(self):
        """
        Get all annotations.
        
        Returns:
            List of Annotation objects
        """
        return self.annotations.copy()
    
    def refresh_annotation_regions(self):
        """
        Refresh all annotation visual regions to match annotation data.
        This is called when annotations are edited on another widget (e.g., spectrogram).
        """
        for annotation in self.annotations:
            if annotation in self.annotation_regions:
                # Update all region items for this annotation to match its current times
                regions_to_update = self.annotation_regions[annotation]
                for region in regions_to_update:
                    region.blockSignals(True)
                    region.setRegion([annotation.start_time, annotation.end_time])
                    region.blockSignals(False)
    
    def load_annotations(self, annotations: List[Annotation]):
        """
        Load annotations and display them.
        
        Args:
            annotations: List of Annotation objects
        """
        # Clear existing
        self.clear_all_annotations()
        
        # Add each annotation
        for annotation in annotations:
            self.annotations.append(annotation)
            self.add_annotation_to_plots(annotation)
        
        self.annotations_changed.emit()
    
    def autoscale_y_axis(self):
        """Autoscale the Y-axis to fit visible data with 5% padding (preserves X-axis range)."""
        for i, plot_widget in enumerate(self.plot_widgets):
            view_box = plot_widget.getViewBox()
            if view_box and i < len(self.plot_items):
                # Get current X-axis range (visible segment)
                x_range = view_box.viewRange()[0]
                x_min, x_max = x_range[0], x_range[1]
                
                # Get the plot data item
                plot_item = self.plot_items[i]
                x_data, y_data = plot_item.getData()
                
                if x_data is not None and y_data is not None and len(y_data) > 0:
                    # Find indices that fall within visible X range
                    mask = (x_data >= x_min) & (x_data <= x_max)
                    visible_y_data = y_data[mask]
                    
                    if len(visible_y_data) > 0:
                        # Calculate min and max with 5% padding
                        y_min = np.min(visible_y_data)
                        y_max = np.max(visible_y_data)
                        
                        # Apply 5% padding to expand range
                        y_range = y_max - y_min
                        if y_range > 0:
                            y_min_scaled = y_min * 1.05
                            y_max_scaled = y_max * 1.05
                            # Ensure we have a reasonable range
                            view_box.setYRange(y_min_scaled, y_max_scaled, padding=0)
                        else:
                            # If min and max are the same, add some padding
                            view_box.setYRange(y_min - 1, y_max + 1, padding=0)
                    else:
                        # Fallback to autoRange if no data in visible range
                        view_box.autoRange(padding=0.02)
                else:
                    # Fallback to autoRange if no data
                    view_box.autoRange(padding=0.02)
                
                # Always preserve the X-axis range
                view_box.setXRange(x_min, x_max, padding=0)
    
    def play_selected_segment(self):
        """Play the selected region segment as audio in a background thread."""
        if self.sensor_data is None or not self.region_items:
            QMessageBox.warning(self, "No Data", "Please load data first.")
            return
        
        try:
            # Get selected region
            start, end = self.region_items[0].getRegion()
            
            # Get data for selected region
            timestamps, data = self.sensor_data.get_time_slice(start, end)
            
            if len(data) == 0:
                QMessageBox.warning(self, "Empty Region", "Please select a valid region to play.")
                return
            
            # Get selected channel from dropdown
            channel_idx = self.channel_combo.currentData() if self.channel_combo else 0
            
            # Use selected channel for playback
            audio_data = data[:, channel_idx]
            
            # Normalize audio to [-1, 1] range to prevent clipping
            max_val = np.max(np.abs(audio_data))
            if max_val > 0:
                audio_data = audio_data / max_val
            
            # Mark as playing and update buttons
            self.is_playing = True
            self.play_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.stop_button.setStyleSheet("background-color: #ffcccc;")
            
            # Update status bar
            status_bar = self.statusBar()
            if status_bar:
                duration = len(audio_data) / self.sensor_data.sample_rate
                status_bar.showMessage(f"Playing segment ({duration:.2f}s)...")
            
            # Start playback in background thread to keep UI responsive
            playback_thread = threading.Thread(
                target=self._play_audio_in_thread,
                args=(audio_data, self.sensor_data.sample_rate),
                daemon=True
            )
            playback_thread.start()
        
        except ImportError:
            QMessageBox.critical(
                self,
                "sounddevice Not Installed",
                "Please install sounddevice:\npip install sounddevice"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Playback Error",
                f"Error playing audio:\n{str(e)}"
            )
            self.is_playing = False
            self.play_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.stop_button.setStyleSheet("")
    
    def _play_audio_in_thread(self, audio_data: np.ndarray, sample_rate: int):
        """Play audio in background thread without blocking UI."""
        try:
            import sounddevice as sd
            sd.play(audio_data, samplerate=int(sample_rate))
            sd.wait()  # Block only this thread, not the UI thread
        except Exception as e:
            print(f"Playback error: {e}")
        finally:
            # Reset button state - only update Qt objects from main thread
            self.is_playing = False
            self.play_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.stop_button.setStyleSheet("")
            # Don't access status bar from background thread - it causes crashes
    
    def stop_playback(self):
        """Stop audio playback."""
        try:
            import sounddevice as sd
            sd.stop()
            self.is_playing = False
            self.play_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.stop_button.setStyleSheet("")
            # Note: Don't try to update status bar from stop_playback
            # as it may be called from background thread
        except Exception as e:
            print(f"Error stopping playback: {e}")
    
    def statusBar(self):
        """Helper to get status bar from main window."""
        window = self.window()
        if hasattr(window, 'statusBar'):
            return window.statusBar()
        return None
