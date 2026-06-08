"""
Annotation panel for managing annotation labels and categories.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QListWidget, QPushButton,
    QHBoxLayout, QInputDialog, QColorDialog, QListWidgetItem, QMessageBox
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QColor, QBrush
from typing import Dict, Optional


class AnnotationPanel(QWidget):
    """
    Panel for managing annotation labels and selecting active annotation category.
    """
    
    # Signal emitted when active label changes
    label_selected = pyqtSignal(str, tuple)  # label_name, color_rgb
    
    # Signal emitted when labels are modified
    labels_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Dictionary mapping label names to colors (RGB tuples)
        self.labels: Dict[str, tuple] = {
            'Label1': (255, 0, 0),      # Red
            'Label2': (0, 255, 0),      # Green
            'Label3': (0, 0, 255),      # Blue
        }
        
        self.active_label: Optional[str] = 'Label1'
        
        self.init_ui()
        self.populate_label_list()
    
    def init_ui(self):
        """Initialize the user interface."""
        main_layout = QVBoxLayout(self)
        
        # Annotation Labels Group
        labels_group = QGroupBox("Annotation Labels")
        labels_layout = QVBoxLayout()
        
        # Label list
        self.label_list = QListWidget()
        self.label_list.itemClicked.connect(self.on_label_clicked)
        self.label_list.itemDoubleClicked.connect(self.edit_label)
        labels_layout.addWidget(self.label_list)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.add_label)
        btn_layout.addWidget(add_btn)
        
        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(self.edit_label)
        btn_layout.addWidget(edit_btn)
        
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(self.remove_label)
        btn_layout.addWidget(remove_btn)
        
        labels_layout.addLayout(btn_layout)
        
        # Change color button
        color_btn = QPushButton("Change Color")
        color_btn.clicked.connect(self.change_label_color)
        labels_layout.addWidget(color_btn)
        
        labels_group.setLayout(labels_layout)
        main_layout.addWidget(labels_group)
        
        # Add stretch
        main_layout.addStretch()
    
    def populate_label_list(self):
        """Populate the label list widget."""
        self.label_list.clear()
        
        for label_name, color in self.labels.items():
            item = QListWidgetItem(label_name)
            
            # Set background color
            qcolor = QColor(*color)
            item.setBackground(QBrush(qcolor))
            
            # Set text color (white for dark backgrounds, black for light)
            luminance = (0.299 * color[0] + 0.587 * color[1] + 0.114 * color[2])
            text_color = QColor(0, 0, 0) if luminance > 128 else QColor(255, 255, 255)
            item.setForeground(QBrush(text_color))
            
            self.label_list.addItem(item)
        
        # Select active label
        if self.active_label:
            for i in range(self.label_list.count()):
                if self.label_list.item(i).text() == self.active_label:
                    self.label_list.setCurrentRow(i)
                    break
    
    def on_label_clicked(self, item: QListWidgetItem):
        """Handle label selection."""
        label_name = item.text()
        self.active_label = label_name
        color = self.labels[label_name]
        self.label_selected.emit(label_name, color)
    
    def add_label(self):
        """Add a new label."""
        label_name, ok = QInputDialog.getText(
            self,
            "Add Label",
            "Enter label name:"
        )
        
        if ok and label_name:
            # Check if label already exists
            if label_name in self.labels:
                QMessageBox.warning(
                    self,
                    "Duplicate Label",
                    f"Label '{label_name}' already exists."
                )
                return
            
            # Add with default color (random-ish)
            import random
            color = (
                random.randint(50, 255),
                random.randint(50, 255),
                random.randint(50, 255)
            )
            self.labels[label_name] = color
            
            # Update UI
            self.populate_label_list()
            self.labels_changed.emit()
    
    def edit_label(self):
        """Edit the selected label name."""
        current_item = self.label_list.currentItem()
        if not current_item:
            return
        
        old_name = current_item.text()
        
        new_name, ok = QInputDialog.getText(
            self,
            "Edit Label",
            "Enter new label name:",
            text=old_name
        )
        
        if ok and new_name and new_name != old_name:
            # Check if new name already exists
            if new_name in self.labels:
                QMessageBox.warning(
                    self,
                    "Duplicate Label",
                    f"Label '{new_name}' already exists."
                )
                return
            
            # Rename label
            color = self.labels[old_name]
            del self.labels[old_name]
            self.labels[new_name] = color
            
            # Update active label if it was renamed
            if self.active_label == old_name:
                self.active_label = new_name
            
            # Update UI
            self.populate_label_list()
            self.labels_changed.emit()
    
    def remove_label(self):
        """Remove the selected label."""
        current_item = self.label_list.currentItem()
        if not current_item:
            return
        
        label_name = current_item.text()
        
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Remove Label",
            f"Remove label '{label_name}'?\n\nExisting annotations with this label will remain but won't have a label category.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            del self.labels[label_name]
            
            # Update active label
            if self.active_label == label_name:
                self.active_label = list(self.labels.keys())[0] if self.labels else None
            
            # Update UI
            self.populate_label_list()
            self.labels_changed.emit()
    
    def change_label_color(self):
        """Change the color of the selected label."""
        current_item = self.label_list.currentItem()
        if not current_item:
            return
        
        label_name = current_item.text()
        current_color = self.labels[label_name]
        
        # Open color dialog
        qcolor = QColorDialog.getColor(QColor(*current_color), self)
        
        if qcolor.isValid():
            new_color = (qcolor.red(), qcolor.green(), qcolor.blue())
            self.labels[label_name] = new_color
            
            # Update UI
            self.populate_label_list()
            self.labels_changed.emit()
    
    def get_active_label(self):
        """
        Get the currently active label and its color.
        
        Returns:
            Tuple of (label_name, color_rgb) or (None, None)
        """
        if self.active_label and self.active_label in self.labels:
            return self.active_label, self.labels[self.active_label]
        return None, None
    
    def get_all_labels(self):
        """
        Get all labels and their colors.
        
        Returns:
            List of tuples (label_name, color_tuple)
        """
        return [(name, color) for name, color in self.labels.items()]
    
    def clear_labels(self):
        """Clear all labels."""
        self.labels.clear()
        self.active_label = None
        self.populate_label_list()
        self.labels_changed.emit()
    
    def add_label(self, label_name: str, color: tuple):
        """
        Add a label programmatically (for config loading).
        
        Args:
            label_name: Name of the label
            color: RGB color tuple
        """
        self.labels[label_name] = color
        self.populate_label_list()
        
        # Set as active if it's the first label
        if not self.active_label:
            self.active_label = label_name
            self.label_selected.emit(label_name, color)
