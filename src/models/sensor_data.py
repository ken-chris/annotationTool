"""
Sensor data model for storing time series data and metadata.
"""
import numpy as np
from typing import Optional, List


class SensorData:
    """
    Container for sensor time series data.
    
    Attributes:
        timestamps: Array of timestamps (seconds)
        data: 2D array of shape (n_samples, n_channels)
        sample_rate: Sampling rate in Hz
        channel_names: List of channel names
        filename: Original filename
    """
    
    def __init__(
        self,
        timestamps: np.ndarray,
        data: np.ndarray,
        sample_rate: float,
        channel_names: Optional[List[str]] = None,
        filename: Optional[str] = None
    ):
        self.timestamps = timestamps
        self.data = data
        self.sample_rate = sample_rate
        self.filename = filename
        
        # Auto-generate channel names if not provided
        if channel_names is None:
            n_channels = data.shape[1]
            self.channel_names = [f"Channel {i+1}" for i in range(n_channels)]
        else:
            self.channel_names = channel_names
    
    @property
    def n_samples(self) -> int:
        """Number of samples."""
        return len(self.timestamps)
    
    @property
    def n_channels(self) -> int:
        """Number of channels."""
        return self.data.shape[1]
    
    @property
    def duration(self) -> float:
        """Duration in seconds."""
        return self.timestamps[-1] - self.timestamps[0]
    
    def get_channel(self, channel_idx: int) -> np.ndarray:
        """Get data for a specific channel."""
        return self.data[:, channel_idx]
    
    def get_time_slice(self, start_time: float, end_time: float):
        """
        Get a time slice of the data.
        
        Args:
            start_time: Start time in seconds
            end_time: End time in seconds
            
        Returns:
            Tuple of (timestamps, data) for the slice
        """
        mask = (self.timestamps >= start_time) & (self.timestamps <= end_time)
        return self.timestamps[mask], self.data[mask]
    
    def apply_channel_names_from_config(self, config_channel_names: list):
        """
        Apply channel names from config, using them in order up to the number of channels.
        Excess config names are ignored, excess channels keep generic names.
        
        Args:
            config_channel_names: List of channel names from config
        """
        if not config_channel_names:
            return
        
        # Apply config channel names up to the number of channels we have
        for i in range(min(len(config_channel_names), len(self.channel_names))):
            self.channel_names[i] = config_channel_names[i]
    
