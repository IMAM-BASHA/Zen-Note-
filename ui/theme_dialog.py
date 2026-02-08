from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QRadioButton, QPushButton, QFrame, QButtonGroup
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

class ThemeExportDialog(QDialog):
    def __init__(self, parent=None, current_theme_mode="light"):
        super().__init__(parent)
        self.setWindowTitle("PDF Export Theme")
        self.setFixedWidth(350)
        self.selected_theme = 0 # 0=Light, 1=Dark
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 1. Title Label
        title = QLabel("Choose PDF Theme:")
        title.setStyleSheet("font-weight: bold; font-size: 11pt;")
        layout.addWidget(title)
        
        # 2. Radio Buttons
        self.radio_light = QRadioButton("Light Theme (White Background)")
        self.radio_dark = QRadioButton("Dark Theme (Dark Background)")
        
        self.radio_light.setStyleSheet("font-size: 10pt; margin-bottom: 5px;")
        self.radio_dark.setStyleSheet("font-size: 10pt;")
        
        self.bg_group = QButtonGroup(self)
        self.bg_group.addButton(self.radio_light, 0)
        self.bg_group.addButton(self.radio_dark, 1)
        
        layout.addWidget(self.radio_light)
        layout.addWidget(self.radio_dark)
        
        # 3. Preview Section
        preview_label = QLabel("Preview:")
        preview_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(preview_label)
        
        self.preview_frame = QFrame()
        self.preview_frame.setFixedHeight(80)
        self.preview_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.preview_frame.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(self.preview_frame)
        
        # 4. Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setHeight = 35
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0; 
                border: 1px solid #d0d0d0; 
                border-radius: 4px; 
                padding: 6px 15px;
            }
            QPushButton:hover { background-color: #e0e0e0; }
        """)
        
        self.export_btn = QPushButton("Export")
        self.export_btn.setHeight = 35
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #007ACC; 
                color: white; 
                border: none; 
                border-radius: 4px; 
                padding: 6px 15px; 
                font-weight: bold;
            }
            QPushButton:hover { background-color: #006bb3; }
        """)
        
        self.cancel_btn.clicked.connect(self.reject)
        self.export_btn.clicked.connect(self.accept)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.export_btn)
        layout.addLayout(btn_layout)
        
        # Connect signals
        self.bg_group.idToggled.connect(self.update_preview)
        
        # Set default
        if current_theme_mode == "dark":
            self.radio_dark.setChecked(True)
        else:
            self.radio_light.setChecked(True)
            
        self.update_preview()
        
    def update_preview(self):
        is_dark = self.radio_dark.isChecked()
        self.selected_theme = 1 if is_dark else 0
        
        if is_dark:
            self.preview_frame.setStyleSheet("""
                QFrame {
                    background-color: #1e1e1e;
                    border: 1px solid #444444;
                    border-radius: 4px;
                }
            """)
        else:
            self.preview_frame.setStyleSheet("""
                QFrame {
                    background-color: #ffffff;
                    border: 1px solid #cccccc;
                    border-radius: 4px;
                }
            """)
            
    def get_selected_theme(self):
        return 1 if self.radio_dark.isChecked() else 0
