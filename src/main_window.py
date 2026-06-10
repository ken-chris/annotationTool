"""
Main application window.
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTabWidget, QFileDialog, QMessageBox, QStatusBar, QMenuBar,
    QGroupBox, QLabel
)
from PyQt6.QtCore import Qt, QTimer, QEvent
from PyQt6.QtGui import QAction, QKeySequence
from typing import Optional
from src.models.sensor_data import SensorData
from src.models.annotation import Annotation
from src.utils.data_loader import load_data, load_annotations_json
from src.utils.export import export_to_json, export_to_csv, save_session, load_session
from src.utils.config import AppConfig
from src.widgets.timeseries_widget import TimeSeriesWidget
from src.widgets.fft_widget import FFTWidget
from src.widgets.spectrogram_widget import SpectrogramWidget
from src.widgets.parameter_panel import ParameterPanel
from src.widgets.annotation_panel import AnnotationPanel


class MainWindow(QMainWindow):
    """Main application window for sensor data annotation."""
    
    def __init__(self):
        super().__init__()
        self.sensor_data: Optional[SensorData] = None
        self.annotations: list[Annotation] = []
        self.current_annotation_label = "Label1"
        self.config: AppConfig = AppConfig.get_default()
        
        # Flag to prevent view sync recursion
        self.is_syncing_views = False
        
        # Shared playback state (only one tab can play at a time)
        # This prevents race conditions when stopping playback from a different tab
        import threading
        self.playback_lock = threading.Lock()
        self.playback_thread_finished = threading.Event()
        self.playback_thread_finished.set()  # Initially set (no playback)
        self.is_playing = False
        self.stop_in_progress = False
        self.active_playback_widget = None  # Track which widget is currently playing
        
        self.init_ui()
        
        # Install event filter for global spacebar handling
        self.installEventFilter(self)
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Sensor Data Annotation Tool")
        self.setGeometry(100, 100, 1400, 800)
        
        # Create menu bar
        self.create_menus()
        
        # Create status bar (use inherited method, don't shadow it)
        self.statusBar().showMessage("Ready")
        
        # Create central widget with splitter
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        
        # Main splitter (left panel | right panel)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel (control panels)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # File info display
        file_info_group = QGroupBox("Loaded Data")
        file_info_layout = QVBoxLayout(file_info_group)
        self.file_info_label = QLabel("No data loaded")
        self.file_info_label.setStyleSheet("color: #666; font-style: italic;")
        self.file_info_label.setWordWrap(True)
        file_info_layout.addWidget(self.file_info_label)
        file_info_group.setMaximumHeight(80)
        left_layout.addWidget(file_info_group)
        
        # Create annotation panel
        self.annotation_panel = AnnotationPanel()
        self.annotation_panel.label_selected.connect(self.on_label_selected)
        left_layout.addWidget(self.annotation_panel)
        
        # Create parameter panel
        self.parameter_panel = ParameterPanel()
        self.parameter_panel.stft_parameters_changed.connect(self.on_stft_parameters_changed)
        self.parameter_panel.fft_parameters_changed.connect(self.on_fft_parameters_changed)
        left_layout.addWidget(self.parameter_panel)
        
        left_layout.addStretch()
        
        # Right panel (tab widget for plots)
        self.tab_widget = QTabWidget()
        
        # Create plot widgets
        self.timeseries_widget = TimeSeriesWidget()
        self.timeseries_widget.region_changed.connect(self.on_region_changed)
        self.timeseries_widget.annotations_changed.connect(self.on_annotations_changed)
        self.timeseries_widget.annotation_selected.connect(self.on_annotation_selected)
        self.timeseries_widget.view_range_changed.connect(self.on_view_range_changed)
        
        # Set initial active label
        label, color = self.annotation_panel.get_active_label()
        if label:
            self.timeseries_widget.set_active_label(label, color)
        
        self.spectrogram_widget = SpectrogramWidget()
        self.spectrogram_widget.view_range_changed.connect(self.on_spectrogram_view_range_changed)
        self.spectrogram_widget.annotations_changed.connect(self.on_spectrogram_annotations_changed)
        self.spectrogram_widget.region_changed.connect(self.on_spectrogram_region_changed)
        self.fft_widget = FFTWidget()
        
        # Add tabs
        self.tab_widget.addTab(self.timeseries_widget, "Time Series")
        self.tab_widget.addTab(self.spectrogram_widget, "Spectrogram")
        self.tab_widget.addTab(self.fft_widget, "FFT")
        
        # Add panels to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(self.tab_widget)
        
        # Set splitter proportions (1:4 ratio)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 4)
        
        main_layout.addWidget(splitter)
    
    def create_menus(self):
        """Create menu bar with actions."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        open_action = QAction("&Open...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        # Load Annotations action
        load_annotations_action = QAction("Load &Annotations...", self)
        load_annotations_action.setShortcut(QKeySequence("Ctrl+L"))
        load_annotations_action.triggered.connect(self.load_annotations)
        file_menu.addAction(load_annotations_action)
        
        file_menu.addSeparator()
        
        # Load Config action
        load_config_action = QAction("Load C&onfig...", self)
        load_config_action.setShortcut(QKeySequence("Ctrl+Shift+O"))
        load_config_action.triggered.connect(self.load_config_file)
        file_menu.addAction(load_config_action)
        
        # Save Config action
        save_config_action = QAction("Save Config &As...", self)
        save_config_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        save_config_action.triggered.connect(self.save_config_file)
        file_menu.addAction(save_config_action)
        
        file_menu.addSeparator()
        
        save_action = QAction("&Save Annotations", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_annotations)
        file_menu.addAction(save_action)
        
        export_action = QAction("&Export Annotations...", self)
        export_action.setShortcut(QKeySequence("Ctrl+E"))
        export_action.triggered.connect(self.export_annotations)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        quit_action = QAction("&Quit", self)
        quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        delete_annotation_action = QAction("&Delete Selected Annotation", self)
        delete_annotation_action.setShortcut(QKeySequence.StandardKey.Delete)
        delete_annotation_action.triggered.connect(self.delete_selected_annotation)
        edit_menu.addAction(delete_annotation_action)
        
        clear_annotations_action = QAction("&Clear All Annotations", self)
        clear_annotations_action.setShortcut(QKeySequence("Ctrl+Shift+D"))
        clear_annotations_action.triggered.connect(self.clear_all_annotations)
        edit_menu.addAction(clear_annotations_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        autoscale_y_action = QAction("Autoscale &Y-Axis", self)
        autoscale_y_action.setShortcut(QKeySequence("Ctrl+Y"))
        autoscale_y_action.triggered.connect(self.autoscale_y_axis)
        view_menu.addAction(autoscale_y_action)
        
        home_selection_action = QAction("&Home Selection", self)
        home_selection_action.setShortcut(QKeySequence("Ctrl+H"))
        home_selection_action.triggered.connect(self.home_selection)
        view_menu.addAction(home_selection_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        feature_ref_action = QAction("&Feature Reference", self)
        feature_ref_action.triggered.connect(self.show_feature_reference)
        help_menu.addAction(feature_ref_action)
        
        help_menu.addSeparator()
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def delete_selected_annotation(self):
        """Delete the currently selected annotation."""
        self.timeseries_widget.delete_selected_annotation()
    
    def clear_all_annotations(self):
        """Clear all annotations from both tabs."""
        self.timeseries_widget.clear_all_annotations()
        self.spectrogram_widget.clear_all_annotations()
    
    def autoscale_y_axis(self):
        """Autoscale the Y-axis for all plots."""
        # Autoscale timeseries Y-axis
        self.timeseries_widget.autoscale_y_axis()
        
        # Autoscale spectrogram Y-axis (frequency axis)
        self.spectrogram_widget.autoscale_y_axis()
    
    def home_selection(self):
        """Move selection to home position (10%-30% of visible segment)."""
        # Get the currently active tab
        if self.tab_widget.currentIndex() == 0:  # Time Series tab
            self.timeseries_widget.home_selection()
        elif self.tab_widget.currentIndex() == 1:  # Spectrogram tab
            self.spectrogram_widget.home_selection()
    
    def eventFilter(self, obj, event):
        """Global event filter to handle spacebar across entire application."""
        if event.type() == QEvent.Type.KeyPress:
            if event.key() == 32 and not event.isAutoRepeat():  # Key code 32 is spacebar
                # Route to the current active widget
                if self.tab_widget.currentIndex() == 0:  # Time Series tab
                    if self.timeseries_widget.is_playing:
                        self.timeseries_widget.stop_playback()
                    else:
                        self.timeseries_widget.play_selected_segment()
                    return True
                elif self.tab_widget.currentIndex() == 1:  # Spectrogram tab
                    if self.spectrogram_widget.is_playing:
                        self.spectrogram_widget.stop_playback()
                    else:
                        self.spectrogram_widget.play_selected_segment()
                    return True
        return super().eventFilter(obj, event)
    
    def open_file(self):
        """Open a data file dialog."""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Open Sensor Data File",
            "",
            "Data Files (*.csv *.npy *.h5 *.hdf5);;CSV Files (*.csv);;NumPy Files (*.npy);;HDF5 Files (*.h5 *.hdf5);;All Files (*)"
        )
        
        if filename:
            self.load_data_file(filename)
    
    def load_annotations(self):
        """Load annotations from a JSON file dialog."""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Load Annotations",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if filename:
            self.load_annotations_file(filename)
    
    def load_annotations_file(self, filename: str):
        """Load annotations from a JSON file and add them to the current view."""
        try:
            self.statusBar().showMessage(f"Loading annotations from {filename}...")
            
            # Load annotations using the new function
            loaded_annotations = load_annotations_json(filename)
            
            if not loaded_annotations:
                QMessageBox.warning(
                    self,
                    "No Annotations",
                    f"No annotations found in {filename}"
                )
                return
            
            # Set sample rate if sensor data is loaded
            if self.sensor_data:
                for annotation in loaded_annotations:
                    annotation.sample_rate = self.sensor_data.sample_rate
            
            # Add loaded annotations to the time series widget
            for annotation in loaded_annotations:
                self.timeseries_widget.annotations.append(annotation)
                self.timeseries_widget.add_annotation_to_plots(annotation)
            
            # Emit annotations changed signal
            self.timeseries_widget.annotations_changed.emit()
            
            # Update status bar
            self.statusBar().showMessage(
                f"Loaded {len(loaded_annotations)} annotations from {filename}"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Loading Annotations",
                f"Could not load annotations from {filename}:\n\n{str(e)}"
            )
            self.statusBar().showMessage("Error loading annotations")

    
    def load_data_file(self, filename: str):
        """Load a data file and update the UI."""
        try:
            self.statusBar().showMessage(f"Loading {filename}...")
            self.sensor_data = load_data(filename)
            
            # Apply channel names from config if available
            if self.config.channel_names:
                self.sensor_data.apply_channel_names_from_config(self.config.channel_names)
            
            # Update file info display in left panel
            import os
            file_name = os.path.basename(self.sensor_data.filename)
            file_info = (
                f"<b>{file_name}</b><br>"
                f"Samples: {self.sensor_data.n_samples:,}<br>"
                f"Channels: {self.sensor_data.n_channels}<br>"
                f"Duration: {self.sensor_data.duration:.2f}s<br>"
                f"Sample Rate: {self.sensor_data.sample_rate:.1f} Hz"
            )
            self.file_info_label.setText(file_info)
            self.file_info_label.setStyleSheet("")  # Remove italic style when data is loaded
            
            # Update status bar with file info
            info_msg = (f"Loaded: {self.sensor_data.filename} | "
                       f"{self.sensor_data.n_samples:,} samples | "
                       f"{self.sensor_data.n_channels} channels | "
                       f"{self.sensor_data.duration:.2f}s | "
                       f"{self.sensor_data.sample_rate:.1f} Hz")
            self.statusBar().showMessage(info_msg)
            
            # Update plot widgets with new data
            self.timeseries_widget.set_data(self.sensor_data)
            self.fft_widget.set_data(self.sensor_data)
            self.spectrogram_widget.set_data(self.sensor_data)
            
            # Update parameter panel with channel names
            self.parameter_panel.update_channel_list(self.sensor_data.channel_names)
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Loading File",
                f"Could not load file:\n{filename}\n\nError: {str(e)}"
            )
            self.statusBar().showMessage("Error loading file")
    
    def save_annotations(self):
        """Save annotations to file."""
        # Get current annotations from widget
        self.annotations = self.timeseries_widget.get_annotations()
        
        if not self.annotations:
            QMessageBox.information(
                self,
                "No Annotations",
                "There are no annotations to save."
            )
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Annotation Session",
            "",
            "JSON Files (*.json)"
        )
        
        if filename:
            try:
                sensor_filename = self.sensor_data.filename if self.sensor_data else None
                save_session(self.annotations, filename, sensor_filename)
                self.statusBar().showMessage(f"Saved {len(self.annotations)} annotations to {filename}")
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error Saving",
                    f"Could not save annotations:\n{str(e)}"
                )
    
    def export_annotations(self):
        """Export annotations to JSON or CSV."""
        # Get current annotations from widget
        self.annotations = self.timeseries_widget.get_annotations()
        
        if not self.annotations:
            QMessageBox.information(
                self,
                "No Annotations",
                "There are no annotations to export."
            )
            return
        
        filename, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export Annotations",
            "",
            "JSON Files (*.json);;CSV Files (*.csv)"
        )
        
        if filename:
            try:
                if selected_filter == "CSV Files (*.csv)" or filename.endswith('.csv'):
                    export_to_csv(self.annotations, filename)
                else:
                    export_to_json(self.annotations, filename)
                
                self.statusBar().showMessage(f"Exported {len(self.annotations)} annotations to {filename}")
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error Exporting",
                    f"Could not export annotations:\n{str(e)}"
                )
    
    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Sensor Data Annotation Tool",
            "<h3>Sensor Data Annotation Tool</h3>"
            "<p>Version 0.1.0</p>"
            "<p>A high-performance tool for annotating time series sensor data "
            "with real-time FFT and STFT visualization.</p>"
            "<p>Built with PyQt6 and PyQtGraph</p>"
        )
    
    def show_feature_reference(self):
        """Show feature reference dialog with keyboard shortcuts."""
        QMessageBox.information(
            self,
            "Feature Reference - Keyboard Shortcuts",
            "<h3>Keyboard Shortcuts & Features</h3>"
            "<p><b>Playback Control:</b></p>"
            "<ul>"
            "<li><b>Spacebar</b> - Toggle playback start/stop for selected segment</li>"
            "</ul>"
            "<p><b>View & Display:</b></p>"
            "<ul>"
            "<li><b>Ctrl+Y</b> - Autoscale Y-axis to fit visible data (with 5% padding)</li>"
            "<li><b>Ctrl+H</b> - Home Selection - Move selection to 10%-30% of visible segment</li>"
            "</ul>"
            "<p><b>Annotation Management:</b></p>"
            "<ul>"
            "<li><b>Delete</b> - Delete selected annotation</li>"
            "<li><b>Ctrl+Shift+D</b> - Clear all annotations (with confirmation)</li>"
            "</ul>"
            "<p><b>File Operations:</b></p>"
            "<ul>"
            "<li><b>Ctrl+O</b> - Open sensor data file</li>"
            "<li><b>Ctrl+S</b> - Save annotations</li>"
            "<li><b>Ctrl+L</b> - Load annotations from file</li>"
            "<li><b>Ctrl+E</b> - Export annotations to CSV/JSON</li>"
            "<li><b>Ctrl+Shift+O</b> - Load configuration file</li>"
            "<li><b>Ctrl+Shift+S</b> - Save configuration file</li>"
            "</ul>"
            "<p><b>Notes:</b></p>"
            "<ul>"
            "<li>Annotations created in either tab (Time Series or Spectrogram) are automatically synced</li>"
            "<li>All keyboard shortcuts work in both Time Series and Spectrogram tabs</li>"
            "</ul>"
        )
    
    def on_region_changed(self, start_time: float, end_time: float):
        """Handle region selection change in time series widget."""
        # Update FFT with selected region (all channels)
        self.fft_widget.update_fft(start_time, end_time)
        
        # Update spectrogram with the new region overlay
        self.spectrogram_widget.set_region(start_time, end_time)
    
    def on_stft_parameters_changed(self, window_size: int, overlap: float, window_type: str,
                                   use_db: bool, db_ref: float, vmin: float, vmax: float):
        """Handle STFT parameter changes."""
        self.spectrogram_widget.set_parameters(window_size, overlap, window_type, use_db, db_ref, vmin, vmax)
        
        db_info = f"dB scale (range: [{vmin}, {vmax}]dB)" if use_db else "linear scale"
        self.statusBar().showMessage(
            f"STFT updated: window={window_size}, overlap={overlap*100:.0f}%, "
            f"type={window_type}, {db_info}"
        )
    
    def on_fft_parameters_changed(self, nperseg: int, window: str):
        """Handle FFT parameter changes."""
        self.fft_widget.set_fft_parameters(nperseg, window)
        self.config.fft.nperseg = nperseg
        self.config.fft.window = window
        self.statusBar().showMessage(f"FFT updated: segment size={nperseg}, window={window}", 2000)
    
    def on_label_selected(self, label_name: str, color: tuple):
        """Handle annotation label selection."""
        self.current_annotation_label = label_name
        self.timeseries_widget.set_active_label(label_name, color)
        self.statusBar().showMessage(f"Active annotation label: {label_name}")
    
    def on_annotations_changed(self):
        """Handle changes to annotations (created, edited, deleted)."""
        # Update main window annotations list
        self.annotations = self.timeseries_widget.get_annotations()
        
        # Update spectrogram with annotations overlay
        self.spectrogram_widget.set_annotations(self.annotations)
        
        # Update status bar
        self.statusBar().showMessage(f"Total annotations: {len(self.annotations)}")
    
    def on_annotation_selected(self, annotation):
        """Handle annotation selection."""
        if annotation:
            self.statusBar().showMessage(
                f"Selected: '{annotation.label}' ({annotation.start_time:.2f}s - {annotation.end_time:.2f}s) | "
                f"Press Delete key to remove"
            )
        else:
            self.statusBar().showMessage("No annotation selected")
    
    def on_view_range_changed(self, x_min: float, x_max: float):
        """Handle view range changes in time series and sync to spectrogram."""
        if self.is_syncing_views:
            return
        
        try:
            self.is_syncing_views = True
            # Update spectrogram x-axis to match time series view
            self.spectrogram_widget.set_x_range(x_min, x_max)
        finally:
            self.is_syncing_views = False
    
    def on_spectrogram_view_range_changed(self, x_min: float, x_max: float):
        """Handle view range changes in spectrogram and sync to time series."""
        if self.is_syncing_views:
            return
        
        try:
            self.is_syncing_views = True
            # Update time series x-axis to match spectrogram view
            if self.timeseries_widget.plot_widgets:
                # Mark as updating to prevent signal recursion
                self.timeseries_widget.is_updating_range = True
                self.timeseries_widget.plot_widgets[0].setXRange(x_min, x_max, padding=0)
                self.timeseries_widget.is_updating_range = False
        finally:
            self.is_syncing_views = False
    
    def on_spectrogram_annotations_changed(self):
        """Handle annotation changes from spectrogram widget."""
        # Get current annotations from spectrogram (they've been edited or created)
        self.annotations = self.spectrogram_widget.annotations
        
        # Update timeseries with the same annotations
        # This will add new annotations created in spectrogram to timeseries
        self.timeseries_widget.load_annotations(self.annotations)
        
        # Update status bar
        self.statusBar().showMessage(f"Total annotations: {len(self.annotations)}")
    
    def on_spectrogram_region_changed(self, start: float, end: float):
        """Handle region changes from spectrogram widget."""
        # Update timeseries region to match spectrogram
        if self.timeseries_widget and hasattr(self.timeseries_widget, 'region_items'):
            if self.timeseries_widget.region_items:
                # Update the first region (they're all synced internally)
                self.timeseries_widget.region_items[0].blockSignals(True)
                self.timeseries_widget.region_items[0].setRegion([start, end])
                self.timeseries_widget.region_items[0].blockSignals(False)
                
                # Update input fields
                self.timeseries_widget.update_inputs_from_region()
    
    def start_playback(self, widget):
        """
        Start playback in the given widget.
        Ensures only one tab can play at a time (prevents sounddevice conflicts).
        """
        # If another tab is playing, stop it first
        if self.is_playing and self.active_playback_widget != widget:
            print(f"[DEBUG] Stopping playback in {self.active_playback_widget.__class__.__name__} before starting in {widget.__class__.__name__}")
            self.active_playback_widget.stop_playback()
        
        # Now start playback in the requested widget
        self.active_playback_widget = widget
        return True
    
    def stop_playback_global(self):
        """
        Stop playback in the active widget (called globally).
        Coordinates across tabs to prevent race conditions.
        """
        if self.is_playing and self.active_playback_widget:
            self.active_playback_widget.stop_playback()
    
    def apply_config(self):
        """Apply current configuration to all widgets."""
        # Apply labels to annotation panel
        self.annotation_panel.clear_labels()
        for label_config in self.config.labels:
            self.annotation_panel.add_label(label_config.name, label_config.color)
        
        # Apply STFT parameters
        self.parameter_panel.set_window_size(self.config.stft.window_size)
        self.parameter_panel.set_overlap(self.config.stft.overlap)
        self.parameter_panel.set_window_type(self.config.stft.window_type)
        self.parameter_panel.set_db_transform(
            self.config.stft.use_db,
            self.config.stft.db_ref,
            self.config.stft.vmin,
            self.config.stft.vmax
        )
        
        # Apply FFT parameters
        self.parameter_panel.set_fft_parameters(self.config.fft.nperseg, self.config.fft.window)
        self.fft_widget.set_fft_parameters(self.config.fft.nperseg, self.config.fft.window)
        
        # Update spectrogram with new parameters
        if self.sensor_data:
            self.on_stft_parameters_changed(
                self.config.stft.window_size,
                self.config.stft.overlap,
                self.config.stft.window_type,
                self.config.stft.use_db,
                self.config.stft.db_ref,
                self.config.stft.vmin,
                self.config.stft.vmax
            )
    
    def load_config_file(self):
        """Load configuration from JSON file."""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Load Configuration",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if filename:
            try:
                import json
                self.config = AppConfig.load(filename)
                
                # If data is already loaded, apply the channel names from the new config
                if self.sensor_data and self.config.channel_names:
                    self.sensor_data.apply_channel_names_from_config(self.config.channel_names)
                    # Update parameter panel with new channel names
                    self.parameter_panel.update_channel_list(self.sensor_data.channel_names)
                
                self.apply_config()
                self.statusBar().showMessage(f"✓ Configuration loaded successfully", 2000)
            except FileNotFoundError:
                self.statusBar().showMessage(f"✗ Configuration file not found: {filename}", 2000)
            except Exception as e:
                self.statusBar().showMessage(f"✗ Error loading configuration: {str(e)}", 2000)
    
    def save_config_file(self):
        """Save current configuration to JSON file."""
        # Update config with current widget values
        self.update_config_from_widgets()
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Configuration",
            "config.json",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if filename:
            try:
                self.config.save(filename)
                self.statusBar().showMessage(f"Configuration saved to {filename}", 3000)
                QMessageBox.information(
                    self,
                    "Config Saved",
                    f"Configuration successfully saved to:\n{filename}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Error saving configuration:\n{str(e)}"
                )
    
    def update_config_from_widgets(self):
        """Update configuration object with current widget values."""
        # Update labels from annotation panel
        self.config.labels = []
        for name, color in self.annotation_panel.get_all_labels():
            from src.utils.config import LabelConfig
            self.config.labels.append(LabelConfig(name, color))
        
        # Update STFT parameters from parameter panel
        params = self.parameter_panel.get_all_parameters()
        self.config.stft.window_size = params['window_size']
        self.config.stft.overlap = params['overlap']
        self.config.stft.window_type = params['window_type']
        self.config.stft.use_db = params['use_db']
        self.config.stft.db_ref = params['db_ref']
        self.config.stft.vmin = params['vmin']
        self.config.stft.vmax = params['vmax']
