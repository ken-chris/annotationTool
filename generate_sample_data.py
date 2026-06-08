"""
Generate sample sensor data for testing the annotation tool.
"""
import numpy as np
import pandas as pd
from pathlib import Path


def generate_sample_data(
    duration: float = 10.0,
    sample_rate: float = 1000.0,
    n_channels: int = 3,
    output_format: str = 'csv',
    output_path: str = 'sample_sensor_data.csv'
):
    """
    Generate synthetic sensor data with multiple frequency components.
    
    Args:
        duration: Duration in seconds
        sample_rate: Sampling rate in Hz
        n_channels: Number of sensor channels
        output_format: 'csv', 'npy', or 'h5'
        output_path: Output file path
    """
    # Generate timestamps
    n_samples = int(duration * sample_rate)
    timestamps = np.linspace(0, duration, n_samples)
    
    # Generate multi-channel data with different frequency components
    data = np.zeros((n_samples, n_channels))
    
    for channel in range(n_channels):
        # Base frequency for this channel
        base_freq = 10 + channel * 5  # 10Hz, 15Hz, 20Hz, etc.
        
        # Add multiple frequency components
        signal = np.sin(2 * np.pi * base_freq * timestamps)
        signal += 0.5 * np.sin(2 * np.pi * (base_freq * 2) * timestamps)  # Harmonic
        signal += 0.3 * np.sin(2 * np.pi * (base_freq * 0.5) * timestamps)  # Sub-harmonic
        
        # Add noise
        noise = np.random.normal(0, 0.1, n_samples)
        signal += noise
        
        # Add a transient event in the middle
        event_start = int(n_samples * 0.4)
        event_end = int(n_samples * 0.6)
        event_freq = base_freq * 3
        signal[event_start:event_end] += 0.7 * np.sin(2 * np.pi * event_freq * timestamps[event_start:event_end])
        
        data[:, channel] = signal
    
    # Save based on format
    if output_format == 'csv':
        # Create DataFrame
        df = pd.DataFrame(data, columns=[f'Channel{i+1}' for i in range(n_channels)])
        df.insert(0, 'timestamp', timestamps)
        df.to_csv(output_path, index=False)
        
    elif output_format == 'npy':
        # Combine timestamps and data
        arr = np.column_stack([timestamps, data])
        np.save(output_path, arr)
        
    elif output_format == 'h5':
        try:
            import h5py
            arr = np.column_stack([timestamps, data])
            with h5py.File(output_path, 'w') as f:
                dset = f.create_dataset('data', data=arr)
                dset.attrs['sample_rate'] = sample_rate
                dset.attrs['channel_names'] = [f'Channel{i+1}' for i in range(n_channels)]
        except ImportError:
            print("h5py not installed. Install with: pip install h5py")
            return
    
    print(f"Generated sample data: {output_path}")
    print(f"Duration: {duration}s, Sample rate: {sample_rate}Hz, Channels: {n_channels}")
    print(f"Total samples: {n_samples:,}")


if __name__ == '__main__':
    # Generate sample files in multiple formats
    Path('sample_data').mkdir(exist_ok=True)
    
    print("Generating sample sensor data...")
    generate_sample_data(
        duration=10.0,
        sample_rate=1000.0,
        n_channels=3,
        output_format='csv',
        output_path='sample_data/sample_sensor_data.csv'
    )
    
    generate_sample_data(
        duration=10.0,
        sample_rate=1000.0,
        n_channels=3,
        output_format='npy',
        output_path='sample_data/sample_sensor_data.npy'
    )
    
    print("\nSample files created in 'sample_data/' directory")
    print("Load these files in the application to test functionality!")
