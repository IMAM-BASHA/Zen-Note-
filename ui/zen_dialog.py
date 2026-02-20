from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QWidget, QFrame, QLineEdit, QComboBox, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, QPoint, QSize, QTimer
from PyQt6.QtGui import QIcon, QFont, QColor
from util.icon_factory import get_premium_icon
import ui.styles as styles

class ZenDialog(QDialog):
    """
    Base class for all modernized application dialogs.
    Features: Frameless window, custom header, theme-aware styling.
    """
    def __init__(self, parent=None, title="Dialog", theme_mode="light"):
        super().__init__(parent)
        self.theme_mode = theme_mode
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Main Container (Rounded Corners)
        self.main_container = QFrame(self)
        self.main_container.setObjectName("ZenDialogContainer")
        
        # Layouts
        self.base_layout = QVBoxLayout(self)
        self.base_layout.setContentsMargins(0, 0, 0, 0)
        self.base_layout.addWidget(self.main_container)
        
        self.layout = QVBoxLayout(self.main_container)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # 1. Custom Header
        self.header = QWidget()
        self.header.setFixedHeight(40)
        self.header_layout = QHBoxLayout(self.header)
        self.header_layout.setContentsMargins(15, 0, 10, 0)
        self.header_layout.setSpacing(10)
        
        # App Branding / Icon
        self.icon_container = QFrame()
        self.icon_container.setObjectName("DialogLogoContainer")
        self.icon_container.setFixedSize(28, 28)
        
        container_layout = QHBoxLayout(self.icon_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.icon_label = QLabel()
        self.icon_label.setPixmap(QIcon("logo_transparent.png").pixmap(18, 18))
        self.icon_label.setFixedSize(18, 18)
        self.icon_label.setScaledContents(True)
        
        container_layout.addWidget(self.icon_label)
        self.header_layout.addWidget(self.icon_container)
        
        # Title
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        self.header_layout.addWidget(self.title_label)
        
        self.header_layout.addStretch()
        
        # Close Button
        self.btn_close = QPushButton("✕")
        self.btn_close.setFixedSize(30, 30)
        self.btn_close.clicked.connect(self.reject)
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.header_layout.addWidget(self.btn_close)
        
        self.layout.addWidget(self.header)
        
        # 2. Content Area
        self.content_container = QWidget()
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(20, 10, 20, 20)
        self.content_layout.setSpacing(15)
        self.layout.addWidget(self.content_container)
        
        # Dragging Logic
        self._drag_pos = None
        
        self._apply_base_theme()

    def _apply_base_theme(self):
        c = styles.ZEN_THEME.get(self.theme_mode, styles.ZEN_THEME["light"])
        is_dark = self.theme_mode == "dark"
        
        # Update Icon Color based on theme if needed, but Zen green is usually fine
        # Update Icon if needed (Pixmap is static, but container bg changes)
        # We use a static transparent logo, so no color swap needed for icon itself.
        # self.icon_label.setPixmap(...) 
        
        # Dialog Container Style
        self.main_container.setStyleSheet(f"""
            QFrame#ZenDialogContainer {{
                background-color: {c['background']};
                border: 1px solid {c['border']};
                border-radius: 12px;
            }}
            QFrame#DialogLogoContainer {{
                background-color: {c['active_item_bg']};
                border-radius: 6px;
                border: 1px solid {c['border']};
            }}
        """)
        
        header_color = c['sidebar_bg'] # Slightly subtle difference or same as bg
        self.header.setStyleSheet(f"""
            QWidget {{
                background-color: {header_color};
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
                border-bottom: 1px solid {c['border']};
            }}
            QLabel {{
                color: {c['foreground']};
                border: none;
            }}
        """)
        
        self.btn_close.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 4px;
                color: {c['muted_foreground']};
                font-size: 14px;
            }}
            QPushButton:hover {{
                background: #EF4444;
                color: white;
            }}
        """)
        
        # Global widget theme within dialog
        self.content_container.setStyleSheet(f"color: {c['foreground']};")

    # Dragging Logic
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Check if click is in header
            if self.header.rect().contains(self.header.mapFromGlobal(event.globalPosition().toPoint())):
                self._drag_pos = event.globalPosition().toPoint()
                event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos:
            delta = event.globalPosition().toPoint() - self._drag_pos
            self.move(self.pos() + delta)
            self._drag_pos = event.globalPosition().toPoint()
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

class ZenInputDialog(ZenDialog):
    """ drop-in replacement for QInputDialog.getText """
    def __init__(self, parent=None, title="Input", label="Enter value:", text="", theme_mode="light"):
        super().__init__(parent, title, theme_mode)
        self.setMinimumWidth(440)
        
        self.label = QLabel(label)
        self.label.setWordWrap(True)
        self.label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.MinimumExpanding)
        self.content_layout.addWidget(self.label)
        
        self.input = QLineEdit(text)
        self.content_layout.addWidget(self.input)
        
        # Robustly set focus after the layout and buttons are established
        QTimer.singleShot(0, self.input.setFocus)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_ok = QPushButton("OK")
        self.btn_ok.clicked.connect(self.accept)
        self.btn_ok.setDefault(True)
        
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_ok)
        self.content_layout.addLayout(btn_layout)
        
        self._apply_input_theme()

    def _apply_input_theme(self):
        c = styles.ZEN_THEME.get(self.theme_mode, styles.ZEN_THEME["light"])
        
        input_style = f"""
            QLineEdit {{
                background-color: {c['secondary']};
                color: {c['foreground']};
                border: 1px solid {c['border']};
                border-radius: 6px;
                padding: 8px;
            }}
            QLineEdit:focus {{
                border: 1px solid {c['primary']};
            }}
        """
        self.input.setStyleSheet(input_style)
        
        btn_base = f"""
            QPushButton {{
                padding: 6px 16px;
                border-radius: 6px;
                font-weight: bold;
            }}
        """
        self.btn_cancel.setStyleSheet(btn_base + f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {c['border']};
                color: {c['foreground']};
            }}
            QPushButton:hover {{
                background: {c['muted']};
            }}
        """)
        
        self.btn_ok.setStyleSheet(btn_base + f"""
            QPushButton {{
                background: {c['primary']};
                color: {c['primary_foreground']};
                border: none;
            }}
            QPushButton:hover {{
                opacity: 0.9;
            }}
        """)

    @staticmethod
    def getText(parent, title, label, text="", theme_mode="light"):
        # Auto-detect theme from parent if possible
        if parent and hasattr(parent, 'theme_mode'):
            theme_mode = parent.theme_mode
        elif parent and hasattr(parent, 'data_manager'):
            theme_mode = parent.data_manager.get_setting("theme_mode", "light")

        dlg = ZenInputDialog(parent, title, label, text, theme_mode)
        if dlg.exec():
            return dlg.input.text(), True
        return "", False

class ZenItemDialog(ZenDialog):
    """ drop-in replacement for QInputDialog.getItem """
    def __init__(self, parent=None, title="Select", label="Choose item:", items=[], current=0, editable=False, theme_mode="light"):
        super().__init__(parent, title, theme_mode)
        self.setFixedWidth(400)
        
        self.label = QLabel(label)
        self.content_layout.addWidget(self.label)
        
        self.combo = QComboBox()
        self.combo.addItems(items)
        self.combo.setCurrentIndex(current)
        self.combo.setEditable(editable)
        self.content_layout.addWidget(self.combo)
        
        # Focus the combobox for immediate selection
        QTimer.singleShot(0, self.combo.setFocus)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_ok = QPushButton("OK")
        self.btn_ok.clicked.connect(self.accept)
        self.btn_ok.setDefault(True)
        
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_ok)
        self.content_layout.addLayout(btn_layout)
        
        self._apply_item_theme()

    def _apply_item_theme(self):
        c = styles.ZEN_THEME.get(self.theme_mode, styles.ZEN_THEME["light"])
        
        combo_style = f"""
            QComboBox {{
                background-color: {c['secondary']};
                color: {c['foreground']};
                border: 1px solid {c['border']};
                border-radius: 6px;
                padding: 8px;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
        """
        self.combo.setStyleSheet(combo_style)
        
        btn_base = f"""
            QPushButton {{
                padding: 6px 16px;
                border-radius: 6px;
                font-weight: bold;
            }}
        """
        self.btn_cancel.setStyleSheet(btn_base + f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {c['border']};
                color: {c['foreground']};
            }}
            QPushButton:hover {{
                background: {c['muted']};
            }}
        """)
        
        self.btn_ok.setStyleSheet(btn_base + f"""
            QPushButton {{
                background: {c['primary']};
                color: {c['primary_foreground']};
                border: none;
            }}
            QPushButton:hover {{
                opacity: 0.9;
            }}
        """)

    @staticmethod
    def getItem(parent, title, label, items, current=0, editable=False, theme_mode="light"):
        if parent and hasattr(parent, 'theme_mode'):
            theme_mode = parent.theme_mode
        elif parent and hasattr(parent, 'data_manager'):
            theme_mode = parent.data_manager.get_setting("theme_mode", "light")

        dlg = ZenItemDialog(parent, title, label, items, current, editable, theme_mode)
        if dlg.exec():
            return dlg.combo.currentText(), True
        return "", False
class PageSizeDialog(ZenDialog):
    """ Dialog for selecting paper sizes with a premium look. """
    def __init__(self, parent=None, current_size="free", theme_mode="light"):
        super().__init__(parent, "Page Size", theme_mode)
        self.setFixedWidth(360)
        
        self.label = QLabel("Select note layout / paper size:")
        self.label.setStyleSheet("font-size: 11px; color: palette(mid); margin-bottom: 5px;")
        self.content_layout.addWidget(self.label)
        
        self.sizes = [
            ("Infinite Scroll (Free Size)", "free", "maximize"),
            ("A4 Paper (Standard)", "a4", "file_text"),
            ("A5 Paper (Small)", "a5", "file_text"),
            ("Legal Paper", "legal", "file_text"),
            ("Letter (US)", "letter", "file_text")
        ]
        
        self.buttons = []
        for label, val, icon_name in self.sizes:
            btn = QPushButton(label)
            btn.setIcon(get_premium_icon(icon_name))
            btn.setIconSize(QSize(18, 18))
            btn.setCheckable(True)
            btn.setChecked(val == current_size)
            btn.setProperty("val", val)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setObjectName("SizeOptionBtn")
            
            # Auto-accept on click for speed
            btn.clicked.connect(lambda checked, v=val: self._on_btn_clicked(v))
            
            self.content_layout.addWidget(btn)
            self.buttons.append(btn)

        # Cancel button at bottom
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        footer_layout.addWidget(self.btn_cancel)
        self.content_layout.addLayout(footer_layout)
        
        self._apply_size_theme()
        self.selected_size = current_size

    def _on_btn_clicked(self, val):
        self.selected_size = val
        self.accept()

    def _apply_size_theme(self):
        c = styles.ZEN_THEME.get(self.theme_mode, styles.ZEN_THEME["light"])
        
        btn_style = f"""
            QPushButton#SizeOptionBtn {{
                text-align: left;
                padding: 12px 15px;
                border: 1px solid {c['border']};
                border-radius: 8px;
                background-color: {c['secondary']};
                color: {c['foreground']};
                font-size: 13px;
            }}
            QPushButton#SizeOptionBtn:hover {{
                background-color: {c['muted']};
                border: 1px solid {c['primary']};
            }}
            QPushButton#SizeOptionBtn:checked {{
                background-color: {c['active_item_bg']};
                border: 2px solid {c['primary']};
                font-weight: bold;
            }}
        """
        for btn in self.buttons:
            btn.setStyleSheet(btn_style)
            
        self.btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {c['muted_foreground']};
                padding: 5px 10px;
            }}
            QPushButton:hover {{
                text-decoration: underline;
            }}
        """)

    @staticmethod
    def getPageSize(parent, current_size="free", theme_mode="light"):
        if parent and hasattr(parent, 'theme_mode'):
            theme_mode = parent.theme_mode
        elif parent and hasattr(parent, 'data_manager'):
            theme_mode = parent.data_manager.get_setting("theme_mode", "light")

        dlg = PageSizeDialog(parent, current_size, theme_mode)
        if dlg.exec():
            return dlg.selected_size, True
        return current_size, False
