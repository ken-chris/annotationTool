"""
Annotation data model for storing labeled regions.
"""
from dataclasses import dataclass, field
from typing import Tuple, Optional
from PyQt6.QtGui import QColor


@dataclass
class Annotation:
    """
    Represents a labeled time region.
    
    Attributes:
        label: Annotation label/category
        start_time: Start time in seconds
        end_time: End time in seconds
        color: RGB color tuple or QColor
        notes: Optional notes about the annotation
        sample_rate: Sample rate in Hz (for converting to sample numbers)
    """
    label: str
    start_time: float
    end_time: float
    color: Tuple[int, int, int] = (255, 0, 0)  # Default red
    notes: str = ""
    sample_rate: Optional[float] = field(default=None, hash=False, compare=False)
    
    def __hash__(self):
        """Hash based on object identity, not mutable fields."""
        return id(self)
    
    def __eq__(self, other):
        """Equality based on object identity."""
        return self is other
    
    @property
    def duration(self) -> float:
        """Duration of the annotation in seconds."""
        return self.end_time - self.start_time
    
    @property
    def start_sample(self) -> Optional[int]:
        """Start sample number (if sample_rate is available)."""
        if self.sample_rate is not None:
            return int(self.start_time * self.sample_rate)
        return None
    
    @property
    def end_sample(self) -> Optional[int]:
        """End sample number (if sample_rate is available)."""
        if self.sample_rate is not None:
            return int(self.end_time * self.sample_rate)
        return None
    
    @property
    def n_samples(self) -> Optional[int]:
        """Number of samples in the annotation (if sample_rate is available)."""
        if self.sample_rate is not None:
            return int(self.duration * self.sample_rate)
        return None
    
    def contains(self, time: float) -> bool:
        """Check if a time point is within this annotation."""
        return self.start_time <= time <= self.end_time
    
    def overlaps(self, other: 'Annotation') -> bool:
        """Check if this annotation overlaps with another."""
        return not (self.end_time < other.start_time or self.start_time > other.end_time)
    
    def to_dict(self):
        """Convert to dictionary for JSON export."""
        result = {
            'label': self.label,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': self.duration,
            'color': self.color,
            'notes': self.notes
        }
        
        # Add sample information if available
        if self.sample_rate is not None:
            result['sample_rate'] = self.sample_rate
            result['start_sample'] = self.start_sample
            result['end_sample'] = self.end_sample
            result['n_samples'] = self.n_samples
        
        return result
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create annotation from dictionary."""
        return cls(
            label=data['label'],
            start_time=data['start_time'],
            end_time=data['end_time'],
            color=tuple(data.get('color', (255, 0, 0))),
            notes=data.get('notes', ''),
            sample_rate=data.get('sample_rate')
        )
    
    def __repr__(self):
        return (f"Annotation(label='{self.label}', "
                f"start={self.start_time:.2f}s, "
                f"end={self.end_time:.2f}s)")
