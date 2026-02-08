from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QSpacerItem, QSizePolicy, QApplication,
    QToolButton, QComboBox, QSpinBox
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
        
        # App Logo & Title (REMOVED in Phase 47 refinement as it is redundant with Sidebar)
        # self.logo_label = QLabel()
        # self.logo_label.setPixmap(QIcon("logo_transparent.png").pixmap(18, 18))
        # self.logo_label.setFixedSize(18, 18)
        # self.logo_label.setScaledContents(True)
        # self.layout.addWidget(self.logo_label)
        
        # self.title_label = QLabel("Zen Notes")
        # self.title_label.setStyleSheet('font-weight: bold; font-family: "Inter", sans-serif;')
        # self.layout.addWidget(self.title_label)
        
        # self.layout.addSpacing(10)
        
        # Editor Toolbar Container (Left aligned)
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
        
        # Base Style (Will be updated in set_theme_mode)
        btn.setProperty("is_close", is_close)
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
                # Apply appropriate style based on type
                if isinstance(item, (QComboBox, QSpinBox)):
                    item.setStyleSheet(self._get_input_style())
                elif isinstance(item, QToolButton):
                    item.setStyleSheet(self._get_toolbar_btn_style())
            elif isinstance(item, QAction):
                # Create a button for the action
                btn = QPushButton()
                btn.setDefault(False)
                btn.setAutoDefault(False)
                btn.setIcon(item.icon())
                btn.setToolTip(item.toolTip())
                # btn.setText(item.text()) # Optional if icon exists
                btn.clicked.connect(item.trigger)
                btn.setFixedSize(26, 26) # Slightly more compact
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                
                # Checkable Logic
                if item.isCheckable():
                    btn.setCheckable(True)
                    btn.setChecked(item.isChecked())
                    # Disconnect any old connections if necessary, but for now simple setup
                    item.toggled.connect(btn.setChecked)
                    
                # Apply Style (Theme-Aware)
                btn.setProperty("class", "ToolbarBtn")
                btn.setStyleSheet(self._get_toolbar_btn_style())
                
                self.toolbar_layout.addWidget(btn)
                
            elif item == "SEPARATOR":
                # Create a visual separator
                line = QLabel()
                line.setFixedWidth(1)
                line.setFixedHeight(16)
                line.setProperty("class", "ToolbarSeparator")
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

    def _get_toolbar_btn_style(self, mode="light"):
        is_dark = mode == "dark"
        hover_bg = "rgba(255,255,255,0.1)" if is_dark else "rgba(0,0,0,0.05)"
        checked_bg = "rgba(255,255,255,0.15)" if is_dark else "rgba(0,0,0,0.1)"
        
        return f"""
            QPushButton, QToolButton {{
                background: transparent;
                border: none;
                border-radius: 4px;
                padding: 2px;
            }}
            QPushButton:hover, QToolButton:hover {{
                background: {hover_bg};
            }}
            QPushButton:checked, QToolButton:checked {{
                background: {checked_bg};
            }}
            QToolButton::menu-button {{
                border: none;
                width: 12px;
            }}
        """

    def _get_input_style(self, mode="light"):
        c = styles.ZEN_THEME.get(mode, styles.ZEN_THEME["light"])
        is_dark = mode == "dark"
        bg = c['secondary']
        fg = c['foreground']
        border = c['border']
        
        return f"""
            QComboBox, QSpinBox {{
                background-color: {bg};
                color: {fg};
                border: 1px solid {border};
                border-radius: 4px;
                padding: 2px 4px;
                font-size: 11px;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                border: none;
                background: transparent;
            }}
        """

    def set_theme_mode(self, mode):
        """Update styles based on theme."""
        c = styles.ZEN_THEME.get(mode, styles.ZEN_THEME["light"])
        is_dark = mode == "dark"
        
        # 1. Main Bar
        self.setStyleSheet(f"""
            CustomTitleBar {{
                background-color: {c['background']}; 
                border-bottom: 1px solid {c['border']};
            }}
            QLabel.ToolbarSeparator {{
                background-color: {c['border']};
            }}
        """)
        
        # 2. Window Control Buttons
        btn_color = c['muted_foreground']
        hover_bg = c['accent']
        hover_fg = c['accent_foreground']
        
        win_btn_style = f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                color: {btn_color};
            }}
            QPushButton:hover {{
                background: {hover_bg};
                color: {hover_fg};
            }}
        """
        self.btn_min.setStyleSheet(win_btn_style)
        self.btn_max.setStyleSheet(win_btn_style)
        
        # Close button has unique hover
        close_style = win_btn_style + """
            QPushButton:hover {
                background: #EF4444;
                color: white;
            }
        """
        self.btn_close.setStyleSheet(close_style)

        # 3. Toolbar Widgets (Update existing)
        toolbar_style = self._get_toolbar_btn_style(mode)
        input_style = self._get_input_style(mode)
        
        for i in range(self.toolbar_layout.count()):
            widget = self.toolbar_layout.itemAt(i).widget()
            if isinstance(widget, (QPushButton, QToolButton)):
                widget.setStyleSheet(toolbar_style)
            elif isinstance(widget, (QComboBox, QSpinBox)):
                widget.setStyleSheet(input_style)
