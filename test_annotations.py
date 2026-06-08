"""
Test script to demonstrate annotation functionality.

Run this script after generating sample data with generate_sample_data.py
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from PyQt6.QtWidgets import QApplication, QMessageBox
from src.main_window import MainWindow

def main():
    """Run the annotation demo."""
    app = QApplication(sys.argv)
    
    window = MainWindow()
    window.show()
    
    # Show instructions
    QMessageBox.information(
        window,
        "Annotation Demo",
        "<h3>Annotation Functionality</h3>"
        "<p><b>Steps to test annotations:</b></p>"
        "<ol>"
        "<li>Click <b>File → Open</b> and load sample data (use generate_sample_data.py first)</li>"
        "<li>In the <b>Time Series</b> tab, drag the blue region selector to select a time range</li>"
        "<li>Select an annotation label from the <b>Annotation Labels</b> panel on the left</li>"
        "<li>Click <b>Create Annotation from Region</b> button</li>"
        "<li>The annotation will appear as a colored overlay on all channel plots</li>"
        "<li>You can drag annotation regions to resize them</li>"
        "<li>Right-click an annotation region for edit/delete options</li>"
        "<li>Use <b>File → Export Annotations</b> to save annotations as JSON/CSV</li>"
        "</ol>"
        "<p><b>Features:</b></p>"
        "<ul>"
        "<li>Multiple annotation labels with custom colors</li>"
        "<li>Drag to resize annotations</li>"
        "<li>Overlap detection warnings</li>"
        "<li>Add notes to annotations (via context menu)</li>"
        "<li>Export annotations for further analysis</li>"
        "</ul>"
    )
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
