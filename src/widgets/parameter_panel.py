"""
Parameter control panel for STFT and FFT configuration.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QLabel, QSpinBox, 
    QSlider, QComboBox, QPushButton, QFormLayout, QCheckBox,
    QDoubleSpinBox
)
from PyQt6.QtCore import pyqtSignal, Qt


class ParameterPanel(QWidget):
    """
    Panel for controlling STFT and FFT parameters.
    """
    
    # Signal emitted when STFT parameters change
    stft_parameters_changed = pyqtSignal(int, float, str, bool, float, float, float)  # window_size, overlap, window_type, use_db, db_ref, vmin, vmax
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        main_layout = QVBoxLayout(self)
        
        # STFT Parameters Group
        stft_group = QGroupBox("STFT Parameters")
        stft_layout = QFormLayout()
        
        # Window size (FFT size)
        self.window_size_spin = QSpinBox()
        self.window_size_spin.setMinimum(64)
        self.window_size_spin.setMaximum(8192)
        self.window_size_spin.setValue(256)
        self.window_size_spin.setSingleStep(64)
        self.window_size_spin.setToolTip("FFT window size in samples")
        stft_layout.addRow("Window Size:", self.window_size_spin)
        
        # Overlap percentage
        overlap_layout = QVBoxLayout()
        self.overlap_slider = QSlider(Qt.Orientation.Horizontal)
        self.overlap_slider.setMinimum(0)
        self.overlap_slider.setMaximum(90)
        self.overlap_slider.setValue(50)
        self.overlap_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.overlap_slider.setTickInterval(10)
        self.overlap_slider.setToolTip("Window overlap percentage")
        
        self.overlap_label = QLabel("50%")
        self.overlap_slider.valueChanged.connect(
            lambda val: self.overlap_label.setText(f"{val}%")
        )
        
        overlap_layout.addWidget(self.overlap_slider)
        overlap_layout.addWidget(self.overlap_label)
        stft_layout.addRow("Overlap:", overlap_layout)
        
        # Window type
        self.window_type_combo = QComboBox()
        self.window_type_combo.addItems(['hann', 'hamming', 'blackman', 'bartlett'])
        self.window_type_combo.setCurrentText('hann')
        self.window_type_combo.setToolTip("Window function type")
        stft_layout.addRow("Window Type:", self.window_type_combo)
        
        stft_group.setLayout(stft_layout)
        main_layout.addWidget(stft_group)
        
        # dB Transform Group
        db_group = QGroupBox("dB Scale Settings")
        db_layout = QFormLayout()
        
        # Use dB transform checkbox
        self.use_db_checkbox = QCheckBox("Apply dB Transform")
        self.use_db_checkbox.setChecked(True)
        self.use_db_checkbox.setToolTip("Convert magnitude to decibel scale: 20*log10(magnitude)")
        self.use_db_checkbox.stateChanged.connect(self.toggle_db_controls)
        db_layout.addRow(self.use_db_checkbox)
        
        # Reference value (epsilon to avoid log(0))
        self.db_ref_spin = QDoubleSpinBox()
        self.db_ref_spin.setMinimum(1e-12)
        self.db_ref_spin.setMaximum(1e6)
        self.db_ref_spin.setValue(1e-10)
        self.db_ref_spin.setDecimals(12)
        self.db_ref_spin.setSingleStep(1e-11)
        self.db_ref_spin.setToolTip("Reference value added to avoid log(0)")
        db_layout.addRow("Reference (ε):", self.db_ref_spin)
        
        # Min dB clipping
        self.vmin_spin = QDoubleSpinBox()
        self.vmin_spin.setMinimum(-200)
        self.vmin_spin.setMaximum(0)
        self.vmin_spin.setValue(-80)
        self.vmin_spin.setSuffix(" dB")
        self.vmin_spin.setToolTip("Minimum dB value for display clipping")
        db_layout.addRow("Min dB:", self.vmin_spin)
        
        # Max dB clipping
        self.vmax_spin = QDoubleSpinBox()
        self.vmax_spin.setMinimum(-100)
        self.vmax_spin.setMaximum(100)
        self.vmax_spin.setValue(0)
        self.vmax_spin.setSuffix(" dB")
        self.vmax_spin.setToolTip("Maximum dB value for display clipping")
        db_layout.addRow("Max dB:", self.vmax_spin)
        
        db_group.setLayout(db_layout)
        main_layout.addWidget(db_group)
        
        # Apply button
        apply_stft_btn = QPushButton("Apply STFT Parameters")
        apply_stft_btn.clicked.connect(self.emit_stft_parameters)
        main_layout.addWidget(apply_stft_btn)
        
        # FFT Parameters Group (future expansion)
        fft_group = QGroupBox("FFT Parameters")
        fft_layout = QFormLayout()
        
        # Channel selection for FFT
        self.fft_channel_combo = QComboBox()
        self.fft_channel_combo.addItem("Channel 1")
        self.fft_channel_combo.setToolTip("Select channel for FFT analysis")
        fft_layout.addRow("Channel:", self.fft_channel_combo)
        
        fft_group.setLayout(fft_layout)
        main_layout.addWidget(fft_group)
        
        # Add stretch to push everything to the top
        main_layout.addStretch()
    
    def toggle_db_controls(self, state):
        """Enable/disable dB-related controls based on checkbox state."""
        enabled = (state == Qt.CheckState.Checked.value)
        self.db_ref_spin.setEnabled(enabled)
        self.vmin_spin.setEnabled(enabled)
        self.vmax_spin.setEnabled(enabled)
    
    def emit_stft_parameters(self):
        """Emit signal with current STFT parameters."""
        window_size = self.window_size_spin.value()
        overlap = self.overlap_slider.value() / 100.0  # Convert percentage to fraction
        window_type = self.window_type_combo.currentText()
        use_db = self.use_db_checkbox.isChecked()
        db_ref = self.db_ref_spin.value()
        vmin = self.vmin_spin.value()
        vmax = self.vmax_spin.value()
        
        self.stft_parameters_changed.emit(window_size, overlap, window_type, use_db, db_ref, vmin, vmax)
    
    def get_stft_parameters(self):
        """
        Get current STFT parameters.
        
        Returns:
            Tuple of (window_size, overlap, window_type, use_db, db_ref, vmin, vmax)
        """
        return (
            self.window_size_spin.value(),
            self.overlap_slider.value() / 100.0,
            self.window_type_combo.currentText(),
            self.use_db_checkbox.isChecked(),
            self.db_ref_spin.value(),
            self.vmin_spin.value(),
            self.vmax_spin.value()
        )
    
    def get_all_parameters(self):
        """
        Get all parameters as a dictionary.
        
        Returns:
            Dictionary with all parameters
        """
        return {
            'window_size': self.window_size_spin.value(),
            'overlap': self.overlap_slider.value() / 100.0,
            'window_type': self.window_type_combo.currentText(),
            'use_db': self.use_db_checkbox.isChecked(),
            'db_ref': self.db_ref_spin.value(),
            'vmin': self.vmin_spin.value(),
            'vmax': self.vmax_spin.value()
        }
    
    def set_window_size(self, value: int):
        """Set window size parameter."""
        self.window_size_spin.setValue(value)
    
    def set_overlap(self, value: float):
        """Set overlap parameter (0.0 to 1.0)."""
        self.overlap_slider.setValue(int(value * 100))
    
    def set_window_type(self, window_type: str):
        """Set window type parameter."""
        index = self.window_type_combo.findText(window_type)
        if index >= 0:
            self.window_type_combo.setCurrentIndex(index)
    
    def set_db_transform(self, use_db: bool, db_ref: float = 1e-10, vmin: float = -80, vmax: float = 0):
        """Set dB transform parameters."""
        self.use_db_checkbox.setChecked(use_db)
        self.db_ref_spin.setValue(db_ref)
        self.vmin_spin.setValue(vmin)
        self.vmax_spin.setValue(vmax)
    
    def get_selected_fft_channel(self):
        """
        Get the selected channel index for FFT.
        
        Returns:
            Channel index (0-based)
        """
        return self.fft_channel_combo.currentIndex()
    
    def update_channel_list(self, channel_names: list):
        """
        Update the channel selection combo box.
        
        Args:
            channel_names: List of channel names
        """
        self.fft_channel_combo.clear()
        self.fft_channel_combo.addItems(channel_names)
