"""
Signal processing utilities for FFT and STFT computation.
"""
import numpy as np
from scipy import signal
from typing import Tuple, Optional


def compute_fft(data: np.ndarray, sample_rate: float) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute FFT of a signal.
    
    Args:
        data: 1D array of signal data
        sample_rate: Sampling rate in Hz
        
    Returns:
        Tuple of (frequencies, magnitudes)
    """
    n = len(data)
    
    # Compute FFT
    fft_vals = np.fft.fft(data)
    fft_freq = np.fft.fftfreq(n, 1.0 / sample_rate)
    
    # Take positive frequencies only
    positive_freq_idx = fft_freq > 0
    frequencies = fft_freq[positive_freq_idx]
    magnitudes = np.abs(fft_vals[positive_freq_idx])
    
    return frequencies, magnitudes


def compute_stft(
    data: np.ndarray,
    sample_rate: float,
    window_size: int = 256,
    overlap: float = 0.5,
    window_type: str = 'hann'
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute Short-Time Fourier Transform (STFT) of a signal.
    
    Args:
        data: 1D array of signal data
        sample_rate: Sampling rate in Hz
        window_size: Size of the FFT window (number of samples)
        overlap: Overlap fraction (0.0 to 1.0)
        window_type: Window function type ('hann', 'hamming', 'blackman', 'bartlett')
        
    Returns:
        Tuple of (times, frequencies, spectrogram)
        - times: Time values for each window center
        - frequencies: Frequency values
        - spectrogram: 2D array of shape (n_frequencies, n_times) with magnitude values
    """
    # Calculate hop length from overlap
    hop_length = int(window_size * (1 - overlap))
    
    # Compute STFT
    f, t, Zxx = signal.stft(
        data,
        fs=sample_rate,
        window=window_type,
        nperseg=window_size,
        noverlap=window_size - hop_length
    )
    
    # Get magnitude (absolute value)
    spectrogram = np.abs(Zxx)
    
    return t, f, spectrogram


def find_peaks(frequencies: np.ndarray, magnitudes: np.ndarray, num_peaks: int = 5) -> np.ndarray:
    """
    Find the top N frequency peaks in an FFT.
    
    Args:
        frequencies: Array of frequency values
        magnitudes: Array of magnitude values
        num_peaks: Number of peaks to find
        
    Returns:
        Array of indices of peak frequencies
    """
    # Find peaks using scipy
    peak_indices, _ = signal.find_peaks(magnitudes, height=np.max(magnitudes) * 0.1)
    
    # Sort by magnitude and take top N
    if len(peak_indices) > num_peaks:
        peak_magnitudes = magnitudes[peak_indices]
        top_indices = np.argsort(peak_magnitudes)[-num_peaks:]
        peak_indices = peak_indices[top_indices]
    
    # Sort by frequency
    peak_indices = peak_indices[np.argsort(frequencies[peak_indices])]
    
    return peak_indices


def downsample_signal(data: np.ndarray, factor: int) -> np.ndarray:
    """
    Downsample a signal by a given factor.
    
    Args:
        data: 1D array of signal data
        factor: Downsampling factor
        
    Returns:
        Downsampled array
    """
    if factor <= 1:
        return data
    
    # Use scipy's decimate for anti-aliasing
    try:
        return signal.decimate(data, factor, zero_phase=True)
    except ValueError:
        # If factor is too large, just take every Nth sample
        return data[::factor]


def apply_window(data: np.ndarray, window_type: str = 'hann') -> np.ndarray:
    """
    Apply a window function to signal data.
    
    Args:
        data: 1D array of signal data
        window_type: Type of window ('hann', 'hamming', 'blackman', 'bartlett')
        
    Returns:
        Windowed signal
    """
    n = len(data)
    
    if window_type == 'hann':
        window = np.hanning(n)
    elif window_type == 'hamming':
        window = np.hamming(n)
    elif window_type == 'blackman':
        window = np.blackman(n)
    elif window_type == 'bartlett':
        window = np.bartlett(n)
    else:
        raise ValueError(f"Unknown window type: {window_type}")
    
    return data * window
