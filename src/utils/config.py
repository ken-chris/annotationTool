"""
Configuration file loading and management.
"""
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field


@dataclass
class LabelConfig:
    """Configuration for a single label."""
    name: str
    color: Tuple[int, int, int]
    
    @classmethod
    def from_dict(cls, data: dict) -> 'LabelConfig':
        """Create from dictionary."""
        return cls(
            name=data['name'],
            color=tuple(data['color'])
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'color': list(self.color)
        }


@dataclass
class STFTConfig:
    """Configuration for STFT parameters."""
    window_size: int = 256
    overlap: float = 0.5
    window_type: str = 'hann'
    use_db: bool = True
    db_ref: float = 1e-10
    vmin: float = -80
    vmax: float = 0
    
    @classmethod
    def from_dict(cls, data: dict) -> 'STFTConfig':
        """Create from dictionary."""
        return cls(
            window_size=data.get('window_size', 256),
            overlap=data.get('overlap', 0.5),
            window_type=data.get('window_type', 'hann'),
            use_db=data.get('use_db', True),
            db_ref=data.get('db_ref', 1e-10),
            vmin=data.get('vmin', -80),
            vmax=data.get('vmax', 0)
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'window_size': self.window_size,
            'overlap': self.overlap,
            'window_type': self.window_type,
            'use_db': self.use_db,
            'db_ref': self.db_ref,
            'vmin': self.vmin,
            'vmax': self.vmax
        }


@dataclass
class FFTConfig:
    """Configuration for FFT parameters."""
    nperseg: int = 256
    window: str = 'hann'
    
    @classmethod
    def from_dict(cls, data: dict) -> 'FFTConfig':
        """Create from dictionary."""
        return cls(
            nperseg=data.get('nperseg', 256),
            window=data.get('window', 'hann')
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'nperseg': self.nperseg,
            'window': self.window
        }


@dataclass
class UIConfig:
    """Configuration for UI parameters."""
    plot_height_min: int = 200
    plot_height_max: int = 250
    
    @classmethod
    def from_dict(cls, data: dict) -> 'UIConfig':
        """Create from dictionary."""
        return cls(
            plot_height_min=data.get('plot_height_min', 200),
            plot_height_max=data.get('plot_height_max', 250)
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'plot_height_min': self.plot_height_min,
            'plot_height_max': self.plot_height_max
        }


@dataclass
class DataConfig:
    """Configuration for data parameters."""
    default_sample_rate: float = 100.0
    
    @classmethod
    def from_dict(cls, data: dict) -> 'DataConfig':
        """Create from dictionary."""
        return cls(
            default_sample_rate=data.get('default_sample_rate', 100.0)
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'default_sample_rate': self.default_sample_rate
        }


@dataclass
class AppConfig:
    """Main application configuration."""
    channel_names: List[str] = field(default_factory=list)
    labels: List[LabelConfig] = field(default_factory=list)
    stft: STFTConfig = field(default_factory=STFTConfig)
    fft: FFTConfig = field(default_factory=FFTConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    data: DataConfig = field(default_factory=DataConfig)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'AppConfig':
        """Create from dictionary."""
        channel_names = data.get('channel_names', [])
        labels = [LabelConfig.from_dict(label) for label in data.get('labels', [])]
        stft = STFTConfig.from_dict(data.get('stft', {}))
        fft = FFTConfig.from_dict(data.get('fft', {}))
        ui = UIConfig.from_dict(data.get('ui', {}))
        data_config = DataConfig.from_dict(data.get('data', {}))
        
        return cls(
            channel_names=channel_names,
            labels=labels,
            stft=stft,
            fft=fft,
            ui=ui,
            data=data_config
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'channel_names': self.channel_names,
            'labels': [label.to_dict() for label in self.labels],
            'stft': self.stft.to_dict(),
            'fft': self.fft.to_dict(),
            'ui': self.ui.to_dict(),
            'data': self.data.to_dict()
        }
    
    @classmethod
    def load(cls, filepath: str) -> 'AppConfig':
        """
        Load configuration from JSON file.
        
        Args:
            filepath: Path to config file
            
        Returns:
            AppConfig object
            
        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If file is not valid JSON
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {filepath}")
        
        with open(path, 'r') as f:
            data = json.load(f)
        
        return cls.from_dict(data)
    
    def save(self, filepath: str):
        """
        Save configuration to JSON file.
        
        Args:
            filepath: Path to save config file
        """
        path = Path(filepath)
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def get_default(cls) -> 'AppConfig':
        """Get default configuration."""
        return cls(
            channel_names=[],
            labels=[
                LabelConfig('Label1', (255, 0, 0)),
                LabelConfig('Label2', (0, 255, 0)),
                LabelConfig('Label3', (0, 0, 255)),
            ],
            stft=STFTConfig(),
            fft=FFTConfig(),
            ui=UIConfig(),
            data=DataConfig()
        )
