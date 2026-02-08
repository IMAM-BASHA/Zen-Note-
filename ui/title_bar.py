from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QSpacerItem, QSizePolicy, QApplication
)
from PyQt6.QtCore import Qt, QSize, QPoint
from PyQt6.QtGui import QIcon, QAction
from util.icon_factory import get_premium_icon
import ui.styles as styles

class CustomTitleBar(QWidget):
    """
    A custom frameless title bar that hosts:
    1. App Icon & Title
    2. Editor Toolbar Actions (Centered/Stretched)
    3. Window Controls (Min, Max, Close)
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(10, 0, 10, 0)
        self.layout.setSpacing(8)
        self.setFixedHeight(40) # Standard sleek height
        
        # 1. App Icon & Title
        self.lbl_icon = QLabel()
        self.lbl_icon.setPixmap(get_premium_icon("leaf", color="#7B9E87").pixmap(18, 18))
        self.layout.addWidget(self.lbl_icon)
        
        self.lbl_title = QLabel("Zen Notes")
        self.lbl_title.setObjectName("TitleBarTitle") # For styling
        self.lbl_title.setStyleSheet("font-weight: 600; font-size: 13px; font-family: 'Segoe UI', sans-serif;")
        self.layout.addWidget(self.lbl_title)
        
        # Spacer to separate title from toolbar
        self.title_spacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.layout.addItem(self.title_spacer)
        
        # 2. Toolbar Container (Where editor actions go)
        self.toolbar_container = QWidget()
        self.toolbar_layout = QHBoxLayout(self.toolbar_container)
        self.toolbar_layout.setContentsMargins(0, 0, 0, 0)
        self.toolbar_layout.setSpacing(4)
        self.toolbar_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.layout.addWidget(self.toolbar_container, 1) # Stretch factor 1 to take available space
        
        # Spacer to push window controls to right
        self.right_spacer = QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.layout.addItem(self.right_spacer)

        # 3. Window Controls
        self.btn_min = self._create_window_btn("─", self.minimize_window, "Minimize")
        self.btn_max = self._create_window_btn("☐", self.toggle_maximize, "Maximize")
        self.btn_close = self._create_window_btn("✕", self.close_window, "Close", is_close=True)
        
        # Dragging State
        self._drag_pos = None

    def _create_window_btn(self, text, callback, tooltip, is_close=False):
        btn = QPushButton(text)
        btn.setFixedSize(30, 30)
        btn.setToolTip(tooltip)
        btn.clicked.connect(callback)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Base Style
        base_style = """
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                color: #888;
            }
            QPushButton:hover {
                background: #E0E0E0;
                color: #000;
            }
        """
        if is_close:
            base_style += """
                QPushButton:hover {
                    background: #EF4444;
                    color: white;
                }
            """
        btn.setStyleSheet(base_style)
        self.layout.addWidget(btn)
        return btn

    def set_editor_toolbar_actions(self, actions):
        """Populate the center toolbar area with actions from the editor."""
        # Clear existing
        # (For now assuming one-time setup, but robust for switching)
        while self.toolbar_layout.count():
            item = self.toolbar_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
                
        for item in actions:
            if isinstance(item, QWidget):
                self.toolbar_layout.addWidget(item)
            elif isinstance(item, QAction):
                # Create a button for the action
                btn = QPushButton()
                btn.setDefault(False)
                btn.setAutoDefault(False)
                btn.setIcon(item.icon())
                btn.setToolTip(item.toolTip())
                # btn.setText(item.text()) # Optional if icon exists
                btn.clicked.connect(item.trigger)
                btn.setFixedSize(28, 28)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                
                # Checkable Logic
                if item.isCheckable():
                    btn.setCheckable(True)
                    btn.setChecked(item.isChecked())
                    # Disconnect any old connections if necessary, but for now simple setup
                    item.toggled.connect(btn.setChecked)
                    
                # Apply Style
                btn.setProperty("class", "ToolbarBtn") # For external stylesheet
                btn.setStyleSheet("""
                    QPushButton {
                        background: transparent;
                        border: none;
                        border-radius: 4px;
                        padding: 4px;
                    }
                    QPushButton:hover {
                        background: rgba(0,0,0,0.05);
                    }
                    QPushButton:checked {
                        background: rgba(0,0,0,0.1);
                    }
                """)
                
                self.toolbar_layout.addWidget(btn)
                
            elif item == "SEPARATOR":
                # Create a visual separator
                line = QLabel()
                line.setFixedWidth(1)
                line.setFixedHeight(16)
                line.setStyleSheet("background-color: #DDD;")
                self.toolbar_layout.addWidget(line)

    # Window Control Actions
    def minimize_window(self):
        self.window().showMinimized()

    def toggle_maximize(self):
        if self.window().isMaximized():
            self.window().showNormal()
            self.btn_max.setText("☐")
        else:
            self.window().showMaximized()
            self.btn_max.setText("❐")

    def close_window(self):
        self.window().close()

    # Dragging Logic
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos:
            delta = event.globalPosition().toPoint() - self._drag_pos
            self.window().move(self.window().pos() + delta)
            self._drag_pos = event.globalPosition().toPoint()
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        
    def mouseDoubleClickEvent(self, event):
        # Maximize on double click
        self.toggle_maximize()

    def set_theme_mode(self, mode):
        """Update styles based on theme."""
        c = styles.ZEN_THEME.get(mode, styles.ZEN_THEME["light"])
        
        # Background
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {c['background']}; 
                border-bottom: 1px solid {c['border']};
            }}
             QLabel#TitleBarTitle {{
                color: {c['foreground']};
            }}
        """)
        
        # Update Icons/buttons if needed
