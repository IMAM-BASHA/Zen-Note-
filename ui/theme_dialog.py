from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, 
    QRadioButton, QPushButton, QFrame, QButtonGroup
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
import ui.styles as styles
from ui.zen_dialog import ZenDialog

class ThemeExportDialog(ZenDialog):
    def __init__(self, parent=None, current_theme_mode="light"):
        # Auto-detect theme
        theme_mode = "light"
        if parent and hasattr(parent, 'theme_mode'):
            theme_mode = parent.theme_mode
        elif parent and hasattr(parent, 'data_manager'):
            theme_mode = parent.data_manager.get_setting("theme_mode", "light")

        super().__init__(parent, title="PDF Export Theme", theme_mode=theme_mode)
        self.setFixedWidth(380)
        self.selected_theme = 0 # 0=Light, 1=Dark
        
        self.setup_ui_local()
        self.apply_theme_local()
        
        # Set default
        if current_theme_mode == "dark":
            self.radio_dark.setChecked(True)
        else:
            self.radio_light.setChecked(True)
            
        self.update_preview()
        
    def setup_ui_local(self):
        # 1. Title Label
        title = QLabel("Choose theme for your PDF document:")
        title.setStyleSheet("color: gray; font-size: 11px;")
        self.content_layout.addWidget(title)
        
        # 2. Radio Buttons
        self.radio_light = QRadioButton("Light Theme (Crisp & Professional)")
        self.radio_dark = QRadioButton("Dark Theme (Modern & Eye-Friendly)")
        
        self.radio_light.setCursor(Qt.CursorShape.PointingHandCursor)
        self.radio_dark.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.bg_group = QButtonGroup(self)
        self.bg_group.addButton(self.radio_light, 0)
        self.bg_group.addButton(self.radio_dark, 1)
        
        self.content_layout.addWidget(self.radio_light)
        self.content_layout.addWidget(self.radio_dark)
        
        # 3. Preview Section
        preview_label = QLabel("Visual Preview")
        preview_label.setStyleSheet("font-weight: bold; margin-top: 5px; font-size: 12px;")
        self.content_layout.addWidget(preview_label)
        
        self.preview_frame = QFrame()
        self.preview_frame.setFixedHeight(100)
        self.preview_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.content_layout.addWidget(self.preview_frame)
        
        # 4. Buttons
        btn_layout = QHBoxLayout()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        
        self.export_btn = QPushButton("Confirm Export")
        self.export_btn.clicked.connect(self.accept)
        self.export_btn.setDefault(True)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.export_btn)
        self.content_layout.addLayout(btn_layout)
        
        # Connect signals
        self.bg_group.idToggled.connect(self.update_preview)
        
    def update_preview(self):
        is_dark = self.radio_dark.isChecked()
        self.selected_theme = 1 if is_dark else 0
        
        if is_dark:
            self.preview_frame.setStyleSheet("""
                QFrame {
                    background-color: #1C1917;
                    border: 2px solid #D97706;
                    border-radius: 8px;
                }
            """)
        else:
            self.preview_frame.setStyleSheet("""
                QFrame {
                    background-color: #FFFFFF;
                    border: 2px solid #7B9E87;
                    border-radius: 8px;
                }
            """)
            
    def get_selected_theme(self):
        return 1 if self.radio_dark.isChecked() else 0

    def apply_theme_local(self):
        c = styles.ZEN_THEME.get(self.theme_mode, styles.ZEN_THEME["light"])
        
        radio_style = f"color: {c['foreground']}; font-size: 13px; padding: 5px;"
        self.radio_light.setStyleSheet(radio_style)
        self.radio_dark.setStyleSheet(radio_style)
        
        btn_base = f"""
            QPushButton {{
                padding: 8px 20px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 13px;
            }}
        """
        self.export_btn.setStyleSheet(btn_base + f"""
            QPushButton {{
                background-color: {c['primary']};
                color: {c['primary_foreground']};
                border: none;
            }}
            QPushButton:hover {{ opacity: 0.9; }}
        """)
        
        self.cancel_btn.setStyleSheet(btn_base + f"""
            QPushButton {{
                background-color: transparent;
                color: {c['foreground']};
                border: 1px solid {c['border']};
            }}
            QPushButton:hover {{ background-color: {c['muted']}; }}
        """)
