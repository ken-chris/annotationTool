"""
Spectrogram viewer widget for STFT visualization.
"""
import pyqtgraph as pg
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QLabel, 
    QPushButton, QComboBox, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from typing import Optional, List, Dict
import numpy as np
import threading
from src.models.sensor_data import SensorData
from src.models.annotation import Annotation
from src.utils.signal_processing import compute_stft


class SpectrogramWidget(QWidget):
    """
    Widget for displaying STFT spectrogram (time-frequency heatmap).
    Each channel displayed in a separate plot.
    """
    
    # Signal emitted when the view range changes (pan/zoom)
    view_range_changed = pyqtSignal(float, float)  # x_min, x_max
    # Signal emitted when annotations change
    annotations_changed = pyqtSignal()
    # Signal emitted when the blue region changes
    region_changed = pyqtSignal(float, float)  # start, end
    # Signal emitted when playback finishes (thread-safe)
    playback_finished = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.sensor_data: Optional[SensorData] = None
        self.plot_widgets: List[pg.PlotWidget] = []
        self.image_items: List[pg.ImageItem] = []
        self.color_bars: List[pg.ColorBarItem] = []
        
        # Annotations and regions
        self.annotations: List[Annotation] = []
        self.annotation_regions: Dict[Annotation, List[tuple]] = {}  # List of (plot_widget, region_item) tuples
        self.region_items: List[tuple] = []  # List of (plot_widget, region_item) tuples
        self.selected_annotation: Optional[Annotation] = None
        self.active_label: str = "Label1"
        self.active_color: tuple = (255, 0, 0)
        
        # Audio playback state
        self.is_playing: bool = False
        self.play_button: Optional[QPushButton] = None
        self.stop_button: Optional[QPushButton] = None
        self.channel_combo: Optional[QComboBox] = None
        
        # STFT parameters
        self.window_size = 256
        self.overlap = 0.5
        self.window_type = 'hann'
        self.use_db = True
        self.db_ref = 1e-10
        self.vmin = -80
        self.vmax = 0
        
        # Flag to prevent signal recursion
        self.is_updating_range = False
        
        # Set focus policy so this widget can receive key events
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        self.init_ui()
        
        # Connect playback finished signal
        self.playback_finished.connect(self.on_playback_finished)
    
    def init_ui(self):
        """Initialize the user interface."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Controls layout
        controls_layout = QHBoxLayout()
        
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
        
        # Home selection button
        home_selection_btn = QPushButton("Home Selection")
        home_selection_btn.clicked.connect(self.home_selection)
        home_selection_btn.setToolTip("Move selection to 10%-30% of currently visible segment")
        home_selection_btn.setMaximumWidth(140)
        controls_layout.addWidget(home_selection_btn)
        
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
        
        # Overall info panel at bottom
        self.overall_info = QLabel()
        self.overall_info.setMaximumHeight(30)
        self.overall_info.setStyleSheet("background-color: #f0f0f0; padding: 5px;")
        main_layout.addWidget(self.overall_info)
    
    def set_data(self, sensor_data: SensorData):
        """
        Store reference to sensor data and compute spectrogram.
        
        Args:
            sensor_data: SensorData object
        """
        self.sensor_data = sensor_data
        self.clear_plots()
        
        # Create a plot for each channel
        for i in range(sensor_data.n_channels):
            # Create plot widget
            plot_widget = pg.PlotWidget()
            plot_widget.setBackground('w')
            plot_widget.setLabel('left', f'{sensor_data.channel_names[i]} - Frequency', units='Hz')
            
            # Only show x-axis label on last plot
            if i == sensor_data.n_channels - 1:
                plot_widget.setLabel('bottom', 'Time', units='s')
            else:
                plot_widget.getAxis('bottom').setStyle(showValues=False)
            
            plot_widget.setMinimumHeight(200)
            plot_widget.setMaximumHeight(400)
            
            # Create image item for this channel
            image_item = pg.ImageItem()
            plot_widget.addItem(image_item)
            
            # Create color bar
            color_bar = pg.ColorBarItem(
                values=(0, 1),
                colorMap='viridis'
            )
            # Position color bar on the right side
            color_bar.setImageItem(image_item)
            
            # Store references
            self.plot_widgets.append(plot_widget)
            self.image_items.append(image_item)
            self.color_bars.append(color_bar)
            
            # Add to layout
            self.plots_layout.addWidget(plot_widget)
        
        # Link x-axes of all plots
        if len(self.plot_widgets) > 1:
            for i in range(1, len(self.plot_widgets)):
                self.plot_widgets[i].setXLink(self.plot_widgets[0])
        
        # Connect to view range changes on the first plot
        if self.plot_widgets:
            view_box = self.plot_widgets[0].getViewBox()
            view_box.sigRangeChanged.connect(self.on_view_range_changed)
        
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
        
        # Compute spectrograms
        self.update_all_spectrograms()
    
    def set_x_range(self, x_min: float, x_max: float):
        """
        Set the x-axis range (time range) for all spectrogram plots.
        Blocks signals to prevent recursion during programmatic updates.
        
        Args:
            x_min: Minimum time value
            x_max: Maximum time value
        """
        if self.is_updating_range:
            return  # Prevent recursion
        
        try:
            self.is_updating_range = True
            
            for plot_widget in self.plot_widgets:
                view_box = plot_widget.getViewBox()
                # Block signals during range update
                view_box.sigRangeChanged.disconnect()
                plot_widget.setXRange(x_min, x_max, padding=0)
                # Reconnect signal
                view_box.sigRangeChanged.connect(self.on_view_range_changed)
        finally:
            self.is_updating_range = False
    
    def on_view_range_changed(self):
        """Handle view range changes (pan/zoom) and emit signal."""
        if self.is_updating_range or not self.plot_widgets:
            return
        
        # Get the current x-axis range from the first plot
        view_box = self.plot_widgets[0].getViewBox()
        x_range = view_box.viewRange()[0]  # Returns [[xmin, xmax], [ymin, ymax]]
        
        # Emit signal with the new range
        self.view_range_changed.emit(x_range[0], x_range[1])
    
    def home_selection(self):
        """Move the blue selection to 10%-30% of the currently visible segment."""
        if not self.region_items:
            return
        
        # Get the current visible x-axis range from the first plot
        if not self.plot_widgets:
            return
        
        view_box = self.plot_widgets[0].getViewBox()
        x_range = view_box.viewRange()[0]  # Returns [xmin, xmax]
        x_min, x_max = x_range[0], x_range[1]
        
        # Calculate segment size and position from 10%-30% of the visible segment
        segment_size = x_max - x_min
        start = x_min + segment_size * 0.1
        end = x_min + segment_size * 0.3
        
        # Update all regions
        for plot_widget, region_item in self.region_items:
            region_item.setRegion([start, end])
    
    def clear_plots(self):
        """Clear all existing plots."""
        while self.plots_layout.count():
            item = self.plots_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.plot_widgets.clear()
        self.image_items.clear()
        self.color_bars.clear()
    
    def set_parameters(self, window_size: int, overlap: float, window_type: str, 
                      use_db: bool = True, db_ref: float = 1e-10, 
                      vmin: float = -80, vmax: float = 0):
        """
        Update STFT parameters and recompute spectrogram (preserves view range).
        
        Args:
            window_size: FFT window size in samples
            overlap: Overlap fraction (0.0 to 1.0)
            window_type: Window function type ('hann', 'hamming', 'blackman', etc.)
            use_db: Whether to apply dB transform
            db_ref: Reference value for dB calculation (epsilon to avoid log(0))
            vmin: Minimum dB value for clipping
            vmax: Maximum dB value for clipping
        """
        # Save current view ranges before updating
        saved_view_ranges = []
        for plot_widget in self.plot_widgets:
            view_box = plot_widget.getViewBox()
            view_range = view_box.viewRange()
            saved_view_ranges.append(view_range)
        
        self.window_size = window_size
        self.overlap = overlap
        self.window_type = window_type
        self.use_db = use_db
        self.db_ref = db_ref
        self.vmin = vmin
        self.vmax = vmax
        
        # Recompute spectrograms with new parameters
        if self.sensor_data is not None:
            self.update_all_spectrograms()
        
        # Restore view ranges
        for i, plot_widget in enumerate(self.plot_widgets):
            if i < len(saved_view_ranges):
                x_range, y_range = saved_view_ranges[i]
                plot_widget.setXRange(x_range[0], x_range[1], padding=0)
                plot_widget.setYRange(y_range[0], y_range[1], padding=0)
    
    def update_all_spectrograms(self):
        """Compute and display STFT spectrograms for all channels."""
        if self.sensor_data is None:
            return
        
        for i in range(self.sensor_data.n_channels):
            self.update_spectrogram_for_channel(i)
        
        # Update overall info
        db_status = f", dB scale (ref={self.db_ref:.0e}, range=[{self.vmin}, {self.vmax}]dB)" if self.use_db else ", linear scale"
        self.overall_info.setText(
            f"STFT Parameters: window={self.window_size}, "
            f"overlap={self.overlap*100:.0f}%, type={self.window_type}{db_status}"
        )
    
    def update_spectrogram_for_channel(self, channel_idx: int):
        """
        Compute and display STFT spectrogram for a specific channel.
        
        Args:
            channel_idx: Index of channel to visualize
        """
        if self.sensor_data is None or channel_idx >= len(self.plot_widgets):
            return
        
        plot_widget = self.plot_widgets[channel_idx]
        image_item = self.image_items[channel_idx]
        color_bar = self.color_bars[channel_idx]
        
        # Get channel data
        channel_data = self.sensor_data.get_channel(channel_idx)
        
        # Compute STFT
        times, frequencies, spectrogram = compute_stft(
            channel_data,
            self.sensor_data.sample_rate,
            window_size=self.window_size,
            overlap=self.overlap,
            window_type=self.window_type
        )
        
        # Apply dB transform if enabled
        if self.use_db:
            # Convert to dB scale for better visualization
            spectrogram_transformed = 20 * np.log10(spectrogram + self.db_ref)
            # Clip to specified range
            spectrogram_transformed = np.clip(spectrogram_transformed, self.vmin, self.vmax)
            color_label = 'Magnitude (dB)'
        else:
            # Use linear scale
            spectrogram_transformed = spectrogram
            color_label = 'Magnitude'
        
        # Set image data (transpose for correct orientation)
        image_item.setImage(spectrogram_transformed.T, autoLevels=True)
        
        # Set color map
        self.set_colormap_for_channel(channel_idx, 'viridis')
        
        # Scale and position the image to match time and frequency axes
        time_min, time_max = times[0], times[-1]
        freq_min, freq_max = frequencies[0], frequencies[-1]
        
        # Calculate scale factors
        time_scale = (time_max - time_min) / spectrogram_transformed.shape[1]
        freq_scale = (freq_max - freq_min) / spectrogram_transformed.shape[0]
        
        # Set transform to position and scale the image correctly
        image_item.setTransform(
            pg.QtGui.QTransform.fromScale(time_scale, freq_scale)
        )
        image_item.setPos(time_min, freq_min)
        
        # Update axes ranges
        plot_widget.setXRange(time_min, time_max, padding=0)
        plot_widget.setYRange(freq_min, freq_max, padding=0)
        
        # Update color bar range
        vmin_actual, vmax_actual = spectrogram_transformed.min(), spectrogram_transformed.max()
        color_bar.setLevels((vmin_actual, vmax_actual))
    
    def set_colormap_for_channel(self, channel_idx: int, colormap_name: str):
        """
        Set the colormap for a specific channel's spectrogram.
        
        Args:
            channel_idx: Index of channel
            colormap_name: Name of colormap
        """
        if channel_idx >= len(self.image_items):
            return
        
        image_item = self.image_items[channel_idx]
        color_bar = self.color_bars[channel_idx]
        
        try:
            cmap = pg.colormap.get(colormap_name, source='matplotlib')
            image_item.setColorMap(cmap)
            color_bar.setColorMap(cmap)
        except:
            # Fallback to default
            cmap = pg.colormap.get('viridis', source='matplotlib')
            image_item.setColorMap(cmap)
            color_bar.setColorMap(cmap)
    
    def set_colormap(self, colormap_name: str):
        """
        Set the colormap for all channel spectrograms.
        
        Args:
            colormap_name: Name of colormap ('viridis', 'plasma', 'jet', etc.)
        """
        for i in range(len(self.image_items)):
            self.set_colormap_for_channel(i, colormap_name)
    
    def set_region(self, start: float, end: float):
        """Add or update the blue region overlay on all plots."""
        if not self.plot_widgets or self.sensor_data is None:
            return
        
        # Remove existing regions from their specific plots
        for plot_widget, region in self.region_items:
            try:
                plot_widget.removeItem(region)
            except:
                pass
        self.region_items.clear()
        
        # Create a separate region item for each plot
        for plot_widget in self.plot_widgets:
            region = pg.LinearRegionItem(
                values=[start, end],
                brush=pg.mkBrush(100, 100, 200, 50),
                pen=pg.mkPen(color=(100, 100, 200), width=2),
                movable=True
            )
            # Set higher z-value so it's drawn on top of annotations
            region.setZValue(1000)
            
            # Connect to region change events
            region.sigRegionChanged.connect(self.on_region_changed_internal)
            
            plot_widget.addItem(region)
            self.region_items.append((plot_widget, region))
    
    def set_annotations(self, annotations: List[Annotation]):
        """Display annotations as overlay regions on all plots."""
        if not self.plot_widgets or self.sensor_data is None:
            # Still update the annotations list even if we can't display them
            self.annotations = list(annotations)
            return
        
        # Update internal annotations list
        self.annotations = list(annotations)
        
        # Clear existing annotations from their specific plots
        for ann_regions in self.annotation_regions.values():
            for plot_widget, region in ann_regions:
                try:
                    plot_widget.removeItem(region)
                except:
                    pass
        self.annotation_regions.clear()
        
        # Add new annotation regions
        for annotation in annotations:
            regions = []
            color_rgb = annotation.color if isinstance(annotation.color, tuple) else (255, 0, 0)
            
            # Create a separate region for each plot (movable for editing)
            for plot_widget in self.plot_widgets:
                region = pg.LinearRegionItem(
                    values=[annotation.start_time, annotation.end_time],
                    brush=pg.mkBrush(color_rgb[0], color_rgb[1], color_rgb[2], 30),
                    pen=pg.mkPen(color=color_rgb, width=2),
                    movable=True  # Allow dragging to edit annotation times
                )
                
                # Connect to update handler when region is moved/resized
                region.sigRegionChanged.connect(
                    lambda rgn=region, ann=annotation: self.on_annotation_region_changed(ann, rgn)
                )
                
                # Connect to finish handler to emit signal after drag ends
                region.sigRegionChangeFinished.connect(
                    lambda rgn=region, ann=annotation: self.on_annotation_region_change_finished(ann, rgn)
                )
                
                plot_widget.addItem(region)
                regions.append((plot_widget, region))
            
            self.annotation_regions[annotation] = regions
    
    def play_selected_segment(self):
        """Play the selected region segment as audio in a background thread."""
        if self.sensor_data is None or not self.region_items:
            QMessageBox.warning(self, "No Data", "Please set a region first.")
            return
        
        try:
            # Get region bounds from first region item (tuple of plot_widget, region)
            plot_widget, region = self.region_items[0]
            start, end = region.getRegion()
            
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
            # Emit signal to notify main thread - thread-safe
            self.playback_finished.emit()
    
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
    
    def on_playback_finished(self):
        """Handle playback finished signal from background thread (runs on main thread)."""
        self.is_playing = False
        if self.play_button:
            self.play_button.setEnabled(True)
        if self.stop_button:
            self.stop_button.setEnabled(False)
            self.stop_button.setStyleSheet("")
    
    def statusBar(self):
        """Helper to get status bar from main window."""
        window = self.window()
        if hasattr(window, 'statusBar'):
            return window.statusBar()
        return None
    
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
        
        # Sync all regions for this annotation (across all plots)
        if annotation in self.annotation_regions:
            for plot_widget, other_region in self.annotation_regions[annotation]:
                if other_region != region:
                    other_region.blockSignals(True)
                    other_region.setRegion([start, end])
                    other_region.blockSignals(False)
        
        # Don't emit annotations_changed here - it would cause set_annotations to be called
        # which recreates all regions and causes a jump during dragging.
        # The timeseries will update when the user finishes editing.
    
    def on_annotation_region_change_finished(self, annotation: Annotation, region: pg.LinearRegionItem):
        """
        Handle when annotation region drag finishes (mouse release).
        This is when we emit the signal to update other widgets.
        
        Args:
            annotation: The annotation being modified
            region: The LinearRegionItem that was changed
        """
        # Emit change signal now that drag is finished
        # This will update the timeseries and other widgets
        self.annotations_changed.emit()
    
    def on_region_changed_internal(self, region: pg.LinearRegionItem):
        """
        Handle changes to the blue region (drag to resize/move).
        Syncs all copies across all plots and emits region_changed signal.
        
        Args:
            region: The LinearRegionItem that was changed
        """
        start, end = region.getRegion()
        
        # Sync all regions (block signals to prevent recursion)
        for plot_widget, other_region in self.region_items:
            if other_region != region:
                other_region.blockSignals(True)
                other_region.setRegion([start, end])
                other_region.blockSignals(False)
        
        # Emit signal to notify main window so timeseries can update
        self.region_changed.emit(start, end)
    
    def autoscale_y_axis(self):
        """Autoscale the Y-axis (frequency axis) to fit visible data with 5% padding (preserves X-axis range)."""
        for i, plot_widget in enumerate(self.plot_widgets):
            view_box = plot_widget.getViewBox()
            if view_box and i < len(self.image_items):
                # Get current X-axis range (visible time segment)
                x_range = view_box.viewRange()[0]
                x_min, x_max = x_range[0], x_range[1]
                
                # For spectrogram, we just want to fit the frequency axis to the data
                # The frequency axis should show the full frequency range of the STFT
                # So we'll use autoRange for Y but preserve X
                y_range_before = view_box.viewRange()[1]
                
                # Autorange to get the proper frequency axis fit
                view_box.autoRange(padding=0.02)
                
                # Get the autoranged Y values
                y_range = view_box.viewRange()[1]
                y_min, y_max = y_range[0], y_range[1]
                
                # Apply 5% padding to expand the Y-axis range
                y_center = (y_min + y_max) / 2
                y_range_size = y_max - y_min
                y_min_scaled = y_center - (y_range_size / 2) * 1.05
                y_max_scaled = y_center + (y_range_size / 2) * 1.05                
                view_box.setYRange(y_min_scaled, y_max_scaled, padding=0)
                
                # Always preserve the X-axis range
                view_box.setXRange(x_min, x_max, padding=0)
    
    def set_active_label(self, label: str, color: tuple):
        """Set the active annotation label and color."""
        self.active_label = label
        self.active_color = color
    
    def create_annotation_from_region(self):
        """Create an annotation from the current region."""
        if not self.region_items:
            return
        
        # Get region bounds from first region item (tuple of plot_widget, region)
        plot_widget, region = self.region_items[0]
        start, end = region.getRegion()
        
        from src.models.annotation import Annotation
        annotation = Annotation(
            label=self.active_label,
            start_time=start,
            end_time=end,
            color=self.active_color
        )
        
        # Add to list and display
        self.annotations.append(annotation)
        
        # Display on all plots
        regions = []
        color_rgb = annotation.color if isinstance(annotation.color, tuple) else (255, 0, 0)
        
        for plot_widget in self.plot_widgets:
            region_item = pg.LinearRegionItem(
                values=[annotation.start_time, annotation.end_time],
                brush=pg.mkBrush(color_rgb[0], color_rgb[1], color_rgb[2], 30),
                pen=pg.mkPen(color=color_rgb, width=2),
                movable=True
            )
            
            region_item.sigRegionChanged.connect(
                lambda rgn=region_item, ann=annotation: self.on_annotation_region_changed(ann, rgn)
            )
            region_item.sigRegionChangeFinished.connect(
                lambda rgn=region_item, ann=annotation: self.on_annotation_region_change_finished(ann, rgn)
            )
            
            # Connect click to select
            if hasattr(region_item, 'clicked'):
                region_item.clicked.connect(
                    lambda ann=annotation: self.select_annotation(ann)
                )
            
            plot_widget.addItem(region_item)
            regions.append((plot_widget, region_item))
        
        self.annotation_regions[annotation] = regions
        self.annotations_changed.emit()
    
    def select_annotation(self, annotation: Annotation):
        """Select or deselect an annotation."""
        if self.selected_annotation == annotation:
            self.selected_annotation = None
        else:
            self.selected_annotation = annotation
    
    def delete_selected_annotation(self):
        """Delete the currently selected annotation."""
        if self.selected_annotation is None:
            return
        
        annotation = self.selected_annotation
        
        # Remove visual regions
        if annotation in self.annotation_regions:
            for plot_widget, region in self.annotation_regions[annotation]:
                try:
                    plot_widget.removeItem(region)
                except:
                    pass
            del self.annotation_regions[annotation]
        
        # Remove from list
        if annotation in self.annotations:
            self.annotations.remove(annotation)
        
        self.selected_annotation = None
        self.annotations_changed.emit()
    
    def clear_all_annotations(self):
        """Clear all annotations."""
        if not self.annotations:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "No Annotations", "No annotations to clear.")
            return
        
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self,
            "Clear All Annotations",
            f"Delete all {len(self.annotations)} annotations?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Remove all visual regions
            for annotation in list(self.annotations):
                if annotation in self.annotation_regions:
                    for plot_widget, region in self.annotation_regions[annotation]:
                        try:
                            plot_widget.removeItem(region)
                        except:
                            pass
            
            # Clear storage
            self.annotations.clear()
            self.annotation_regions.clear()
            self.selected_annotation = None
            
            self.annotations_changed.emit()
    
    def keyPressEvent(self, event):
        """Handle key press events for annotation operations."""
        if event.key() == Qt.Key.Key_Delete:
            self.delete_selected_annotation()
            event.accept()
        else:
            super().keyPressEvent(event)
