from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap

class EmptyStateWidget(QWidget):
    """
    A premium placeholder widget displayed when no note is selected.
    Features the brand logo and a subtle instruction text.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("EmptyStateWidget")
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)
        
        # 1. Large Brand Logo
        # utilizing the refined transparency logo
        self.logo_lbl = QLabel()
        pixmap = QIcon("logo_transparent.png").pixmap(128, 128)
        self.logo_lbl.setPixmap(pixmap)
        self.logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Opacity effect via coloring or stylesheet if needed, 
        # but let's try direct rendering first.
        # We can use a graphics effect for opacity if it's too harsh, 
        # but "logo_transparent.png" should be clean.
        
        # 2. Instruction Text
        self.text_lbl = QLabel("Select a note to view")
        self.text_lbl.setObjectName("EmptyStateText")
        self.text_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Initial Style
        self.set_theme_mode("light")
        
        layout.addWidget(self.logo_lbl)
        layout.addWidget(self.text_lbl)
        
    def set_theme_mode(self, mode):
        """
        Adjust style based on theme.
        """
        is_dark = mode in ("dark", "dark_blue", "ocean_depth", "noir_ember")
        text_color = "#A1A1AA" if is_dark else "#52525B" # Zinc 400 vs Zinc 600
        
        self.text_lbl.setStyleSheet(f"""
            QLabel {{
                font-family: "Inter", sans-serif;
                font-size: 16px;
                font-weight: 500;
                color: {text_color}; 
            }}
        """)
