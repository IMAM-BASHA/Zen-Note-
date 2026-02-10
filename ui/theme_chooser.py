"""
Theme Chooser Dialog — "Choose Your Atmosphere"
A premium visual dialog for selecting app themes with custom color support.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QWidget, QGraphicsDropShadowEffect, QSizePolicy, QScrollArea,
    QGridLayout, QColorDialog, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen, QFont, QIcon
import ui.styles as styles
import json


# Theme metadata for display
THEME_META = {
    "light": {
        "name": "Zen Clarity",
        "subtitle": "Clarity & Openness",
        "icon": "☀️",
    },
    "dark": {
        "name": "Creative Amber",
        "subtitle": "Warm & Grounded",
        "icon": "🌙",
    },
    "dark_blue": {
        "name": "Midnight Focus",
        "subtitle": "Focused Precision",
        "icon": "💎",
    },
    "rose": {
        "name": "Rose Garden",
        "subtitle": "Soft Introspection",
        "icon": "🌸",
    },
    "ocean_depth": {
        "name": "Ocean Depth",
        "subtitle": "Deep Focus & Calm",
        "icon": "🌊",
    },
    "forest_sage": {
        "name": "Forest Sage",
        "subtitle": "Grounded & Natural",
        "icon": "🌿",
    },
    "noir_ember": {
        "name": "Noir Ember",
        "subtitle": "Intense & Dramatic",
        "icon": "🔥",
    },
}

THEME_ORDER = ["light", "dark", "dark_blue", "rose", "ocean_depth", "forest_sage", "noir_ember"]


class ThemePreviewWidget(QWidget):
    """Draws a mini color preview of a theme's palette."""
    def __init__(self, theme_key, parent=None):
        super().__init__(parent)
        self.theme_key = theme_key
        self.setFixedSize(120, 76)
    
    def paintEvent(self, event):
        c = styles.ZEN_THEME.get(self.theme_key, styles.ZEN_THEME["light"])
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        bg = QColor(c["background"])
        card = QColor(c["card"])
        primary = QColor(c["primary"])
        border = QColor(c["border"])
        
        # Background
        painter.setBrush(QBrush(bg))
        painter.setPen(QPen(border, 1))
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 8, 8)
        
        # Card blocks
        painter.setBrush(QBrush(card))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(8, 8, 104, 18, 4, 4)
        painter.drawRoundedRect(8, 30, 104, 14, 4, 4)
        
        # Primary accent bar
        painter.setBrush(QBrush(primary))
        painter.drawRoundedRect(8, 50, 50, 18, 4, 4)
        
        # Secondary block
        painter.setBrush(QBrush(card))
        painter.drawRoundedRect(64, 50, 48, 18, 4, 4)
        
        painter.end()


class ThemeCard(QWidget):
    """A single theme card with preview, name, subtitle, and apply button."""
    themeSelected = pyqtSignal(str)
    
    def __init__(self, theme_key, is_active=False, dialog_theme="light", parent=None):
        super().__init__(parent)
        self.theme_key = theme_key
        self.is_active = is_active
        meta = THEME_META.get(theme_key, {"name": theme_key, "subtitle": "", "icon": ""})
        c = styles.ZEN_THEME.get(dialog_theme, styles.ZEN_THEME["light"])
        tc = styles.ZEN_THEME.get(theme_key, styles.ZEN_THEME["light"])
        
        self.setFixedWidth(145)
        self.setFixedHeight(195)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Preview
        preview = ThemePreviewWidget(theme_key)
        layout.addWidget(preview, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Current badge
        if is_active:
            badge = QLabel("● CURRENT")
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setStyleSheet(f"color: {tc['primary']}; font-size: 8px; font-weight: 700; letter-spacing: 0.05em; padding: 1px 0; background: transparent;")
            layout.addWidget(badge)
        
        # Name + Icon row
        name_row = QHBoxLayout()
        name_row.setSpacing(3)
        name_label = QLabel(meta["name"])
        name_label.setStyleSheet(f"color: {c['foreground']}; font-size: 11px; font-weight: 700; background: transparent;")
        name_row.addWidget(name_label)
        icon_dot = QLabel(meta["icon"])
        icon_dot.setStyleSheet("font-size: 11px; background: transparent;")
        name_row.addWidget(icon_dot)
        name_row.addStretch()
        layout.addLayout(name_row)
        
        # Subtitle
        sub = QLabel(meta["subtitle"])
        sub.setStyleSheet(f"color: {c['muted_foreground']}; font-size: 9px; background: transparent;")
        layout.addWidget(sub)
        
        layout.addStretch()
        
        # Button
        btn = QPushButton("Active" if is_active else "Apply")
        btn.setFixedHeight(26)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        if is_active:
            btn.setStyleSheet(f"QPushButton {{ background: {tc['primary']}; color: {tc['primary_foreground']}; border: none; border-radius: 6px; font-weight: 600; font-size: 11px; }}")
            btn.setEnabled(False)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{ background: {c['secondary']}; color: {c['foreground']}; border: 1px solid {c['border']}; border-radius: 6px; font-size: 11px; }}
                QPushButton:hover {{ background: {c['accent']}; border-color: {tc['primary']}; }}
            """)
            btn.clicked.connect(lambda: self.themeSelected.emit(self.theme_key))
        layout.addWidget(btn)
        
        # Card border
        bcolor = tc['primary'] if is_active else c['border']
        bw = 2 if is_active else 1
        self.setStyleSheet(f"ThemeCard {{ background: {c['card']}; border: {bw}px solid {bcolor}; border-radius: 10px; }}")
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and not self.is_active:
            self.themeSelected.emit(self.theme_key)


class ThemeChooserDialog(QDialog):
    """Premium theme selection dialog with 7 themes + custom color builder."""
    themeChosen = pyqtSignal(str)
    
    def __init__(self, current_theme="light", parent=None):
        super().__init__(parent)
        self.current_theme = current_theme
        self.setWindowTitle("Choose Your Atmosphere")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumWidth(680)
        self.setMaximumWidth(780)
        
        c = styles.ZEN_THEME.get(current_theme, styles.ZEN_THEME["light"])
        self._c = c
        
        # Container
        container = QWidget()
        container.setObjectName("ThemeChooserContainer")
        container.setStyleSheet(f"QWidget#ThemeChooserContainer {{ background: {c['background']}; border: 1px solid {c['border']}; border-radius: 16px; }}")
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 60))
        container.setGraphicsEffect(shadow)
        
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.addWidget(container)
        
        main = QVBoxLayout(container)
        main.setContentsMargins(28, 24, 28, 24)
        main.setSpacing(12)
        
        # ── Header ──
        header = QHBoxLayout()
        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title = QLabel("Choose Your Atmosphere")
        title.setStyleSheet(f"color: {c['foreground']}; font-size: 20px; font-weight: 700;")
        title_col.addWidget(title)
        sub = QLabel("Curated palettes designed to enhance your mental state and focus.")
        sub.setStyleSheet(f"color: {c['muted_foreground']}; font-size: 11px;")
        title_col.addWidget(sub)
        header.addLayout(title_col, 1)
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(f"QPushButton {{ background: transparent; color: {c['muted_foreground']}; border: none; font-size: 16px; border-radius: 14px; }} QPushButton:hover {{ background: {c['accent']}; color: {c['foreground']}; }}")
        close_btn.clicked.connect(self.close)
        header.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignTop)
        main.addLayout(header)
        
        # ── Theme Grid (4 per row) ──
        grid = QGridLayout()
        grid.setSpacing(10)
        
        for i, key in enumerate(THEME_ORDER):
            card = ThemeCard(key, is_active=(key == current_theme), dialog_theme=current_theme)
            card.themeSelected.connect(self._on_theme_selected)
            row, col = divmod(i, 4)
            grid.addWidget(card, row, col)
        
        main.addLayout(grid)
        
        # ── Custom Theme Section ──
        sep = self._section_label("CREATE YOUR OWN")
        main.addWidget(sep)
        
        custom_row = QHBoxLayout()
        custom_row.setSpacing(10)
        
        custom_info = QVBoxLayout()
        custom_info.setSpacing(2)
        ci_title = QLabel("🎨 Custom Theme")
        ci_title.setStyleSheet(f"color: {c['foreground']}; font-size: 12px; font-weight: 600;")
        custom_info.addWidget(ci_title)
        ci_sub = QLabel("Pick your own colors for background, text, and accent.")
        ci_sub.setStyleSheet(f"color: {c['muted_foreground']}; font-size: 10px;")
        custom_info.addWidget(ci_sub)
        custom_row.addLayout(custom_info, 1)
        
        custom_btn = QPushButton("Build Theme →")
        custom_btn.setFixedHeight(32)
        custom_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        custom_btn.setStyleSheet(f"""
            QPushButton {{ background: {c['secondary']}; color: {c['foreground']}; border: 1px dashed {c['border']}; border-radius: 8px; padding: 4px 16px; font-size: 11px; font-weight: 500; }}
            QPushButton:hover {{ border-color: {c['primary']}; background: {c['accent']}; }}
        """)
        custom_btn.clicked.connect(self._build_custom_theme)
        custom_row.addWidget(custom_btn)
        main.addLayout(custom_row)
    
    def _section_label(self, text):
        sep = QWidget()
        lay = QHBoxLayout(sep)
        lay.setContentsMargins(0, 4, 0, 0)
        lay.setSpacing(8)
        line1 = QFrame(); line1.setFixedHeight(1); line1.setFixedWidth(20)
        line1.setStyleSheet(f"background: {self._c['border']};")
        lay.addWidget(line1)
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color: {self._c['muted_foreground']}; font-size: 9px; font-weight: 700; letter-spacing: 0.1em;")
        lay.addWidget(lbl)
        line2 = QFrame(); line2.setFixedHeight(1)
        line2.setStyleSheet(f"background: {self._c['border']};")
        lay.addWidget(line2, 1)
        return sep
    
    def _on_theme_selected(self, theme_key):
        self.themeChosen.emit(theme_key)
        self.close()
    
    def _build_custom_theme(self):
        """Open a mini color picker flow to build a custom theme."""
        c = self._c
        dlg = CustomThemeBuilder(dialog_theme=self.current_theme, parent=self)
        dlg.themeBuilt.connect(self._apply_custom_theme)
        dlg.exec()
    
    def _apply_custom_theme(self, theme_data):
        """Register a custom theme and apply it."""
        styles.ZEN_THEME["custom"] = theme_data
        self.themeChosen.emit("custom")
        self.close()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, '_drag_pos'):
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()


class ColorPickerRow(QWidget):
    """A labeled color picker row."""
    colorChanged = pyqtSignal(str, str)  # key, hex
    
    def __init__(self, key, label, default_color, dialog_theme="light", parent=None):
        super().__init__(parent)
        self.key = key
        self.color = default_color
        c = styles.ZEN_THEME.get(dialog_theme, styles.ZEN_THEME["light"])
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        lbl = QLabel(label)
        lbl.setStyleSheet(f"color: {c['foreground']}; font-size: 11px;")
        lbl.setFixedWidth(110)
        layout.addWidget(lbl)
        
        self.swatch = QPushButton()
        self.swatch.setFixedSize(32, 24)
        self.swatch.setCursor(Qt.CursorShape.PointingHandCursor)
        self._update_swatch()
        self.swatch.clicked.connect(self._pick_color)
        layout.addWidget(self.swatch)
        
        self.hex_label = QLabel(default_color)
        self.hex_label.setStyleSheet(f"color: {c['muted_foreground']}; font-size: 10px; font-family: monospace;")
        layout.addWidget(self.hex_label)
        layout.addStretch()
    
    def _update_swatch(self):
        self.swatch.setStyleSheet(f"QPushButton {{ background: {self.color}; border: 1px solid rgba(128,128,128,0.3); border-radius: 4px; }}")
    
    def _pick_color(self):
        color = QColorDialog.getColor(QColor(self.color), self, f"Pick {self.key}")
        if color.isValid():
            self.color = color.name()
            self._update_swatch()
            self.hex_label.setText(self.color)
            self.colorChanged.emit(self.key, self.color)


class CustomThemeBuilder(QDialog):
    """Mini dialog for building a custom theme from color pickers."""
    themeBuilt = pyqtSignal(dict)
    
    def __init__(self, dialog_theme="light", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Build Custom Theme")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(420)
        
        c = styles.ZEN_THEME.get(dialog_theme, styles.ZEN_THEME["light"])
        self._c = c
        self._dialog_theme = dialog_theme
        
        # Start from a copy of the current theme
        self._colors = dict(styles.ZEN_THEME.get(dialog_theme, styles.ZEN_THEME["light"]))
        
        container = QWidget()
        container.setObjectName("CustomBuilder")
        container.setStyleSheet(f"QWidget#CustomBuilder {{ background: {c['background']}; border: 1px solid {c['border']}; border-radius: 14px; }}")
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(0, 0, 0, 50))
        container.setGraphicsEffect(shadow)
        
        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.addWidget(container)
        
        main = QVBoxLayout(container)
        main.setContentsMargins(24, 20, 24, 20)
        main.setSpacing(10)
        
        # Title
        title = QLabel("🎨 Build Your Theme")
        title.setStyleSheet(f"color: {c['foreground']}; font-size: 16px; font-weight: 700;")
        main.addWidget(title)
        
        sub = QLabel("Pick colors to create your unique atmosphere.")
        sub.setStyleSheet(f"color: {c['muted_foreground']}; font-size: 10px; margin-bottom: 4px;")
        main.addWidget(sub)
        
        # Color pickers for key colors
        pickers = [
            ("background", "Background", c["background"]),
            ("foreground", "Text Color", c["foreground"]),
            ("primary", "Accent Color", c["primary"]),
            ("card", "Card/Surface", c["card"]),
            ("sidebar_bg", "Sidebar BG", c["sidebar_bg"]),
            ("border", "Border Color", c["border"]),
        ]
        
        for key, label, default in pickers:
            row = ColorPickerRow(key, label, default, dialog_theme)
            row.colorChanged.connect(self._on_color_changed)
            main.addWidget(row)
        
        # Footer
        main.addSpacing(6)
        footer = QHBoxLayout()
        footer.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet(f"QPushButton {{ background: {c['secondary']}; color: {c['foreground']}; border: 1px solid {c['border']}; border-radius: 6px; padding: 6px 16px; font-size: 11px; }} QPushButton:hover {{ background: {c['accent']}; }}")
        cancel_btn.clicked.connect(self.close)
        footer.addWidget(cancel_btn)
        
        apply_btn = QPushButton("Apply Theme")
        apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        apply_btn.setStyleSheet(f"QPushButton {{ background: {c['primary']}; color: {c['primary_foreground']}; border: none; border-radius: 6px; padding: 6px 20px; font-size: 11px; font-weight: 600; }} QPushButton:hover {{ opacity: 0.9; }}")
        apply_btn.clicked.connect(self._apply)
        footer.addWidget(apply_btn)
        main.addLayout(footer)
    
    def _on_color_changed(self, key, hex_color):
        self._colors[key] = hex_color
        # Auto-derive related colors
        if key == "background":
            self._colors["scrollbar_bg"] = hex_color
        elif key == "foreground":
            self._colors["card_foreground"] = hex_color
            self._colors["popover_foreground"] = hex_color
            self._colors["secondary_foreground"] = hex_color
            self._colors["sidebar_fg"] = hex_color
            self._colors["selection_fg"] = hex_color
        elif key == "primary":
            self._colors["ring"] = hex_color
            self._colors["accent_foreground"] = hex_color
            self._colors["primary_foreground"] = "#FFFFFF"  # default
            # derive accent (translucent)
            qc = QColor(hex_color)
            self._colors["accent"] = f"rgba({qc.red()}, {qc.green()}, {qc.blue()}, 0.12)"
            self._colors["active_item_bg"] = f"rgba({qc.red()}, {qc.green()}, {qc.blue()}, 0.15)"
            self._colors["selection_bg"] = hex_color
        elif key == "card":
            self._colors["popover"] = hex_color
            self._colors["input"] = hex_color
            self._colors["elevated"] = hex_color
        elif key == "sidebar_bg":
            self._colors["sidebar_border"] = hex_color
        elif key == "border":
            self._colors["sidebar_border"] = hex_color
    
    def _apply(self):
        # Fill any missing keys with defaults
        base = dict(styles.ZEN_THEME.get(self._dialog_theme, styles.ZEN_THEME["light"]))
        base.update(self._colors)
        self.themeBuilt.emit(base)
        self.close()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, '_drag_pos'):
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
