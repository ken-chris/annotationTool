"""
Export utilities for annotations.
"""
import json
import csv
from pathlib import Path
from typing import List
from src.models.annotation import Annotation


def export_to_json(annotations: List[Annotation], filepath: str):
    """
    Export annotations to JSON file.
    
    Args:
        annotations: List of Annotation objects
        filepath: Output file path
    """
    data = {
        'annotations': [ann.to_dict() for ann in annotations],
        'count': len(annotations)
    }
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)


def export_to_csv(annotations: List[Annotation], filepath: str):
    """
    Export annotations to CSV file.
    
    Args:
        annotations: List of Annotation objects
        filepath: Output file path
    """
    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Determine if we have sample information
        has_samples = annotations and annotations[0].sample_rate is not None
        
        # Write header
        if has_samples:
            writer.writerow([
                'Label', 'Start Time (s)', 'End Time (s)', 'Duration (s)', 
                'Start Sample', 'End Sample', 'N Samples', 'Sample Rate (Hz)',
                'Color (RGB)', 'Notes'
            ])
        else:
            writer.writerow([
                'Label', 'Start Time (s)', 'End Time (s)', 'Duration (s)', 
                'Color (RGB)', 'Notes'
            ])
        
        # Write data
        for ann in annotations:
            if has_samples:
                writer.writerow([
                    ann.label,
                    f"{ann.start_time:.6f}",
                    f"{ann.end_time:.6f}",
                    f"{ann.duration:.6f}",
                    ann.start_sample,
                    ann.end_sample,
                    ann.n_samples,
                    ann.sample_rate,
                    f"{ann.color}",
                    ann.notes
                ])
            else:
                writer.writerow([
                    ann.label,
                    f"{ann.start_time:.6f}",
                    f"{ann.end_time:.6f}",
                    f"{ann.duration:.6f}",
                    f"{ann.color}",
                    ann.notes
                ])


def load_from_json(filepath: str) -> List[Annotation]:
    """
    Load annotations from JSON file.
    
    Args:
        filepath: Input file path
        
    Returns:
        List of Annotation objects
    """
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    annotations = [Annotation.from_dict(ann_dict) for ann_dict in data['annotations']]
    return annotations


def save_session(annotations: List[Annotation], filepath: str, sensor_filename: str = None):
    """
    Save complete annotation session including metadata.
    
    Args:
        annotations: List of Annotation objects
        filepath: Output file path
        sensor_filename: Original sensor data filename
    """
    data = {
        'sensor_file': sensor_filename,
        'annotation_count': len(annotations),
        'annotations': [ann.to_dict() for ann in annotations]
    }
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)


def load_session(filepath: str) -> tuple[List[Annotation], str]:
    """
    Load annotation session from file.
    
    Args:
        filepath: Input file path
        
    Returns:
        Tuple of (annotations list, sensor_filename)
    """
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    annotations = [Annotation.from_dict(ann_dict) for ann_dict in data['annotations']]
    sensor_filename = data.get('sensor_file')
    
    return annotations, sensor_filename
