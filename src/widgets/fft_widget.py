"""
FFT viewer widget for frequency domain analysis.
"""
import pyqtgraph as pg
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTextEdit, 
    QScrollArea, QHBoxLayout
)
from PyQt6.QtCore import Qt
from typing import Optional, List
import numpy as np
from src.models.sensor_data import SensorData
from src.utils.signal_processing import compute_fft, find_peaks


class FFTWidget(QWidget):
    """
    Widget for displaying FFT (frequency domain) of selected time region.
    Each channel displayed in a separate plot.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.sensor_data: Optional[SensorData] = None
        self.plot_widgets: List[pg.PlotWidget] = []
        self.info_labels: List[QLabel] = []
        
        # FFT parameters
        self.fft_nperseg: int = 256
        self.fft_window: str = 'hann'
        
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
        
        # Overall info panel at bottom
        self.overall_info = QLabel()
        self.overall_info.setMaximumHeight(30)
        self.overall_info.setStyleSheet("background-color: #f0f0f0; padding: 5px;")
        main_layout.addWidget(self.overall_info)
    
    def set_data(self, sensor_data: SensorData):
        """
        Store reference to sensor data and create plot widgets.
        
        Args:
            sensor_data: SensorData object
        """
        self.sensor_data = sensor_data
        self.clear_plots()
        
        # Create a plot for each channel
        colors = ['r', 'g', 'b', 'c', 'm', 'y', 'k']
        
        for i in range(sensor_data.n_channels):
            
            # Create container for this channel (plot + info)
            channel_container = QWidget()
            channel_layout = QVBoxLayout(channel_container)
            channel_layout.setContentsMargins(0, 0, 0, 0)
            channel_layout.setSpacing(2)
            
            # Create plot widget
            plot_widget = pg.PlotWidget()
            plot_widget.setBackground('w')
            plot_widget.showGrid(x=True, y=True, alpha=0.3)
            plot_widget.setLabel('left', f'{sensor_data.channel_names[i]} - Magnitude')
            
            # Only show x-axis label on last plot
            if i == sensor_data.n_channels - 1:
                plot_widget.setLabel('bottom', 'Frequency', units='Hz')
            else:
                plot_widget.getAxis('bottom').setStyle(showValues=False)
            
            plot_widget.setMinimumHeight(200)
            plot_widget.setMaximumHeight(250)  # Match time series and spectrogram
            plot_widget.setAntialiasing(True)
            
            channel_layout.addWidget(plot_widget)
            
            # Info label for this channel's peaks
            info_label = QLabel("No data - select a region in Time Series")
            info_label.setWordWrap(True)
            info_label.setMaximumHeight(60)
            info_label.setStyleSheet("background-color: #f9f9f9; padding: 5px; border: 1px solid #ddd;")
            channel_layout.addWidget(info_label)
            
            # Store references
            self.plot_widgets.append(plot_widget)
            self.info_labels.append(info_label)
            
            # Add to main layout
            self.plots_layout.addWidget(channel_container)
        
        # Link x-axes of all plots
        if len(self.plot_widgets) > 1:
            for i in range(1, len(self.plot_widgets)):
                self.plot_widgets[i].setXLink(self.plot_widgets[0])
    
    def clear_plots(self):
        """Clear all existing plots."""
        while self.plots_layout.count():
            item = self.plots_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.plot_widgets.clear()
        self.info_labels.clear()
    
    def update_fft(self, start_time: float, end_time: float, channel_idx: int = -1):
        """
        Compute and display FFT for the selected time region.
        
        Args:
            start_time: Start time in seconds
            end_time: End time in seconds
            channel_idx: Index of channel to analyze (default: -1 for all channels)
        """
        if self.sensor_data is None:
            return
        
        # Get data slice
        timestamps, data_slice = self.sensor_data.get_time_slice(start_time, end_time)
        
        if len(timestamps) == 0:
            for plot_widget in self.plot_widgets:
                plot_widget.clear()
            for info_label in self.info_labels:
                info_label.setText("No data in selected region")
            self.overall_info.setText("No data in selected region")
            return
        
        # Define colors
        colors = ['r', 'g', 'b', 'c', 'm', 'y', 'k']
        
        # Compute FFT for all channels
        for i in range(self.sensor_data.n_channels):
            plot_widget = self.plot_widgets[i]
            info_label = self.info_labels[i]
            
            # Clear previous plot
            plot_widget.clear()
            
            # Get channel data
            channel_data = data_slice[:, i]
            frequencies, magnitudes = compute_fft(channel_data, self.sensor_data.sample_rate, self.fft_nperseg, self.fft_window)
            
            # Plot FFT with black color for all channels
            plot_widget.plot(
                frequencies,
                magnitudes,
                pen=pg.mkPen(color='k', width=1)
            )
            
            # Find and display peaks
            peak_indices = find_peaks(frequencies, magnitudes, num_peaks=5)
            
            if len(peak_indices) > 0:
                # Mark peaks on plot
                peak_freqs = frequencies[peak_indices]
                peak_mags = magnitudes[peak_indices]
                
                plot_widget.plot(
                    peak_freqs,
                    peak_mags,
                    pen=None,
                    symbol='o',
                    symbolBrush='r',
                    symbolSize=8
                )
                
                # Display peak info
                peak_text = f"<b>{self.sensor_data.channel_names[i]} Peaks:</b> "
                peak_strs = [f"{frequencies[idx]:.2f} Hz" for idx in peak_indices[:3]]
                peak_text += ", ".join(peak_strs)
                if len(peak_indices) > 3:
                    peak_text += f" (+{len(peak_indices)-3} more)"
                info_label.setText(peak_text)
            else:
                info_label.setText(f"{self.sensor_data.channel_names[i]}: No significant peaks found")
        
        # Update overall info
        self.overall_info.setText(
            f"FFT Region: {start_time:.3f}s to {end_time:.3f}s "
            f"({end_time-start_time:.3f}s, {len(timestamps)} samples)"
        )
    
    def set_fft_parameters(self, nperseg: int, window: str):
        """
        Set FFT parameters and trigger recomputation if data exists.
        
        Args:
            nperseg: Number of samples per segment
            window: Window function type
        """
        self.fft_nperseg = nperseg
        self.fft_window = window
