"""
Theme chooser dialog and custom theme builder.
"""
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QColorDialog,
    QFrame,
    QScrollArea,
    QLineEdit,
    QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen, QLinearGradient
import re
import ui.styles as styles


THEME_META = {
    "light": {"name": "Zen Clarity", "subtitle": "Clarity & Openness", "icon": "sun"},
    "forest_sage": {"name": "Forest Sage", "subtitle": "Grounded & Natural", "icon": "leaf"},
    "pearl_mist": {"name": "Pearl Mist", "subtitle": "Soft Gradient Calm", "icon": "mist"},
    "dark": {"name": "Creative Amber", "subtitle": "Warm & Grounded", "icon": "dusk"},
    "aurora_tide": {"name": "Aurora Tide", "subtitle": "Dark Gradient Focus", "icon": "aurora"},
    "ember_dusk": {"name": "Ember Dusk", "subtitle": "Warm Gradient Energy", "icon": "ember"},
    "noir_ember": {"name": "Noir Ember", "subtitle": "Intense & Dramatic", "icon": "noir"},
    "custom": {"name": "My Custom", "subtitle": "Saved Personal Theme", "icon": "custom"},
}


def _theme_order():
    order = [k for k in styles.CURATED_THEME_ORDER if k in styles.ZEN_THEME]
    custom_keys = [k for k in styles.ZEN_THEME if k.startswith("custom_")]
    custom_keys.sort(
        key=lambda k: styles.ZEN_THEME.get(k, {}).get("display_name", k).lower()
    )
    order.extend(custom_keys)
    if "custom" in styles.ZEN_THEME and "custom" not in order:
        order.append("custom")
    return order


def _slugify_theme_name(name):
    if not isinstance(name, str):
        name = ""
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", name.strip().lower()).strip("_")
    return slug or "custom"


def _make_unique_custom_key(name, existing_keys):
    base = f"custom_{_slugify_theme_name(name)}"
    key = base
    idx = 2
    while key in existing_keys:
        key = f"{base}_{idx}"
        idx += 1
    return key


class ThemePreviewWidget(QWidget):
    """Small visual preview for a theme card."""

    def __init__(self, theme_key=None, theme_data=None, parent=None):
        super().__init__(parent)
        self.theme_key = theme_key
        self.theme_data = dict(theme_data) if isinstance(theme_data, dict) else None
        self.setFixedSize(120, 76)

    def set_theme_data(self, theme_data):
        self.theme_data = dict(theme_data) if isinstance(theme_data, dict) else None
        self.update()

    def _theme(self):
        if isinstance(self.theme_data, dict):
            return self.theme_data
        return styles.ZEN_THEME.get(self.theme_key, styles.ZEN_THEME["light"])

    def paintEvent(self, event):
        c = self._theme()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        border = QColor(c.get("border", "#D1D5DB"))
        preview_gradient = c.get("preview_gradient")
        if isinstance(preview_gradient, (list, tuple)) and len(preview_gradient) >= 2:
            g = QLinearGradient(0, 0, self.width(), self.height())
            step = 1.0 / (len(preview_gradient) - 1)
            for i, col in enumerate(preview_gradient):
                g.setColorAt(i * step, QColor(col))
            bg_brush = QBrush(g)
        else:
            bg_brush = QBrush(QColor(c.get("background", "#FFFFFF")))

        painter.setBrush(bg_brush)
        painter.setPen(QPen(border, 1))
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 8, 8)

        card = QColor(c.get("card", "#FFFFFF"))
        primary = QColor(c.get("primary", "#3B82F6"))
        painter.setPen(Qt.PenStyle.NoPen)

        painter.setBrush(QBrush(card))
        painter.drawRoundedRect(8, 8, 104, 18, 4, 4)
        painter.drawRoundedRect(8, 30, 104, 14, 4, 4)
        painter.drawRoundedRect(64, 50, 48, 18, 4, 4)

        painter.setBrush(QBrush(primary))
        painter.drawRoundedRect(8, 50, 50, 18, 4, 4)
        painter.end()


class ThemeCard(QWidget):
    themeSelected = pyqtSignal(str)

    def __init__(self, theme_key, is_active=False, dialog_theme="light", parent=None):
        super().__init__(parent)
        self.theme_key = theme_key
        self.is_active = is_active
        theme_data = styles.ZEN_THEME.get(theme_key, styles.ZEN_THEME["light"])
        fallback_name = theme_key.replace("_", " ").title()
        base_meta = THEME_META.get(theme_key, {"name": fallback_name, "subtitle": "", "icon": ""})
        meta = {
            "name": theme_data.get("display_name", base_meta.get("name", fallback_name)),
            "subtitle": theme_data.get("display_subtitle", base_meta.get("subtitle", "")),
            "icon": base_meta.get("icon", "custom" if theme_key.startswith("custom_") else ""),
        }
        c = styles.ZEN_THEME.get(dialog_theme, styles.ZEN_THEME["light"])
        tc = theme_data

        self.setFixedWidth(145)
        self.setFixedHeight(195)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        preview = ThemePreviewWidget(theme_key)
        layout.addWidget(preview, alignment=Qt.AlignmentFlag.AlignCenter)

        if is_active:
            badge = QLabel("CURRENT")
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setStyleSheet(
                f"color: {tc['primary']}; font-size: 8px; font-weight: 700; letter-spacing: 0.05em; "
                "padding: 1px 0; background: transparent;"
            )
            layout.addWidget(badge)

        name_row = QHBoxLayout()
        name_row.setSpacing(3)
        name_label = QLabel(meta["name"])
        name_label.setStyleSheet(
            f"color: {c['foreground']}; font-size: 11px; font-weight: 700; background: transparent;"
        )
        name_row.addWidget(name_label)
        icon_lbl = QLabel(meta["icon"])
        icon_lbl.setStyleSheet(f"color: {c['muted_foreground']}; font-size: 9px; background: transparent;")
        name_row.addWidget(icon_lbl)
        name_row.addStretch()
        layout.addLayout(name_row)

        sub = QLabel(meta["subtitle"])
        sub.setStyleSheet(f"color: {c['muted_foreground']}; font-size: 9px; background: transparent;")
        layout.addWidget(sub)
        layout.addStretch()

        btn = QPushButton("Active" if is_active else "Apply")
        btn.setFixedHeight(26)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        if is_active:
            btn.setStyleSheet(
                f"QPushButton {{ background: {tc['primary']}; color: {tc['primary_foreground']}; border: none; "
                "border-radius: 6px; font-weight: 600; font-size: 11px; }}"
            )
            btn.setEnabled(False)
        else:
            btn.setStyleSheet(
                f"QPushButton {{ background: {c['secondary']}; color: {c['foreground']}; border: 1px solid {c['border']}; "
                "border-radius: 6px; font-size: 11px; }}"
                f"QPushButton:hover {{ background: {c['accent']}; border-color: {tc['primary']}; }}"
            )
            btn.clicked.connect(lambda: self.themeSelected.emit(self.theme_key))
        layout.addWidget(btn)

        bcolor = tc["primary"] if is_active else c["border"]
        bw = 2 if is_active else 1
        self.setStyleSheet(
            f"ThemeCard {{ background: {c['card']}; border: {bw}px solid {bcolor}; border-radius: 10px; }}"
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and not self.is_active:
            self.themeSelected.emit(self.theme_key)


class ThemeChooserDialog(QDialog):
    """Theme selection dialog with curated defaults and custom theme support."""

    themeChosen = pyqtSignal(str)

    def __init__(self, current_theme="light", parent=None):
        super().__init__(parent)
        self.custom_entries = self._load_custom_entries()
        self.current_theme = styles.resolve_theme_key(current_theme)
        if self.current_theme not in styles.ZEN_THEME:
            self.current_theme = "light"
        self.setWindowTitle("Choose Your Atmosphere")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumWidth(680)
        self.setMaximumWidth(780)

        c = styles.ZEN_THEME.get(self.current_theme, styles.ZEN_THEME["light"])
        self._c = c

        container = QWidget()
        container.setObjectName("ThemeChooserContainer")
        container.setStyleSheet(
            f"QWidget#ThemeChooserContainer {{ background: {c['background']}; border: 1px solid {c['border']}; border-radius: 16px; }}"
        )

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

        header = QHBoxLayout()
        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title = QLabel("Choose Your Atmosphere")
        title.setStyleSheet(f"color: {c['foreground']}; font-size: 20px; font-weight: 700;")
        title_col.addWidget(title)
        sub = QLabel("Curated palettes designed to improve focus, clarity, and visual depth.")
        sub.setStyleSheet(f"color: {c['muted_foreground']}; font-size: 11px;")
        title_col.addWidget(sub)
        header.addLayout(title_col, 1)

        close_btn = QPushButton("x")
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {c['muted_foreground']}; border: none; font-size: 16px; border-radius: 14px; }}"
            f"QPushButton:hover {{ background: {c['accent']}; color: {c['foreground']}; }}"
        )
        close_btn.clicked.connect(self.close)
        header.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignTop)
        main.addLayout(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            f"QScrollArea {{ border: none; background: transparent; }}"
            f"QScrollBar:vertical {{ background: {c['muted']}; width: 8px; border-radius: 4px; }}"
            f"QScrollBar::handle:vertical {{ background: {c.get('scrollbar_handle', c['border'])}; border-radius: 4px; }}"
        )
        scroll_host = QWidget()
        grid = QGridLayout(scroll_host)
        grid.setSpacing(10)
        for i, key in enumerate(_theme_order()):
            card = ThemeCard(key, is_active=(key == self.current_theme), dialog_theme=self.current_theme)
            card.themeSelected.connect(self._on_theme_selected)
            row, col = divmod(i, 4)
            grid.addWidget(card, row, col)
        grid.setRowStretch((len(_theme_order()) // 4) + 1, 1)
        scroll.setWidget(scroll_host)
        scroll.setMinimumHeight(260)
        scroll.setMaximumHeight(430)
        main.addWidget(scroll)

        sep = self._section_label("CREATE YOUR OWN")
        main.addWidget(sep)

        custom_row = QHBoxLayout()
        custom_row.setSpacing(10)

        custom_info = QVBoxLayout()
        custom_info.setSpacing(2)
        ci_title = QLabel("Custom Theme")
        ci_title.setStyleSheet(f"color: {c['foreground']}; font-size: 12px; font-weight: 600;")
        custom_info.addWidget(ci_title)
        ci_sub = QLabel("Build, name, and save as many custom palettes as you want.")
        ci_sub.setStyleSheet(f"color: {c['muted_foreground']}; font-size: 10px;")
        custom_info.addWidget(ci_sub)
        custom_row.addLayout(custom_info, 1)

        custom_btn = QPushButton("Build Theme ->")
        custom_btn.setFixedHeight(32)
        custom_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        custom_btn.setStyleSheet(
            f"QPushButton {{ background: {c['secondary']}; color: {c['foreground']}; border: 1px dashed {c['border']}; "
            "border-radius: 8px; padding: 4px 16px; font-size: 11px; font-weight: 500; }}"
            f"QPushButton:hover {{ border-color: {c['primary']}; background: {c['accent']}; }}"
        )
        custom_btn.clicked.connect(self._build_custom_theme)
        custom_row.addWidget(custom_btn)

        has_custom = any(entry.get("key", "").startswith("custom_") for entry in self.custom_entries)
        if has_custom:
            remove_text = "Remove Current" if str(self.current_theme).startswith("custom_") else "Remove Last"
            remove_btn = QPushButton(remove_text)
            remove_btn.setFixedHeight(32)
            remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            remove_btn.setStyleSheet(
                f"QPushButton {{ background: transparent; color: {c['foreground']}; border: 1px solid {c['border']}; "
                "border-radius: 8px; padding: 4px 12px; font-size: 11px; font-weight: 500; }}"
                "QPushButton:hover { border-color: #EF4444; color: #EF4444; }"
            )
            remove_btn.clicked.connect(self._remove_custom_theme)
            custom_row.addWidget(remove_btn)

        main.addLayout(custom_row)

    def _get_data_manager(self):
        return getattr(self.parent(), "data_manager", None) if self.parent() else None

    def _save_custom_entries(self):
        data_manager = self._get_data_manager()
        if not data_manager:
            return
        # Store only serializable data.
        serializable = []
        for entry in self.custom_entries:
            key = entry.get("key")
            name = entry.get("name")
            theme = entry.get("theme")
            if isinstance(key, str) and key and isinstance(theme, dict):
                serializable.append({"key": key, "name": name or "Custom Theme", "theme": dict(theme)})
        self.custom_entries = serializable
        data_manager.set_setting("custom_themes", serializable)
        data_manager.set_setting("custom_theme_data", serializable[-1]["theme"] if serializable else None)

    def _load_custom_entries(self):
        data_manager = self._get_data_manager()
        entries = []
        used_keys = {k for k in styles.ZEN_THEME if not k.startswith("custom_")}
        changed = False

        raw_entries = []
        if data_manager:
            saved_entries = data_manager.get_setting("custom_themes", [])
            if isinstance(saved_entries, list):
                raw_entries = saved_entries
            elif saved_entries:
                changed = True

            legacy = data_manager.get_setting("custom_theme_data")
            if isinstance(legacy, dict) and legacy and not raw_entries:
                legacy_name = legacy.get("display_name", "My Custom")
                raw_entries = [{"name": legacy_name, "theme": legacy}]
                changed = True

        for idx, item in enumerate(raw_entries):
            if not isinstance(item, dict):
                changed = True
                continue

            theme_data = item.get("theme")
            if not isinstance(theme_data, dict):
                changed = True
                continue

            name = str(item.get("name") or theme_data.get("display_name") or f"Custom Theme {idx + 1}").strip()
            if not name:
                name = f"Custom Theme {idx + 1}"
                changed = True

            key = str(item.get("key") or "").strip()
            if not key.startswith("custom_"):
                key = _make_unique_custom_key(name, used_keys)
                changed = True
            if key in used_keys:
                key = _make_unique_custom_key(name, used_keys)
                changed = True
            used_keys.add(key)

            theme_copy = dict(theme_data)
            theme_copy["display_name"] = name
            theme_copy.setdefault("display_subtitle", "Custom Theme")
            styles.ZEN_THEME[key] = theme_copy
            entries.append({"key": key, "name": name, "theme": theme_copy})

        # Remove stale single-key custom from older builds.
        if "custom" in styles.ZEN_THEME and not any(e.get("key") == "custom" for e in entries):
            styles.ZEN_THEME.pop("custom", None)
            changed = True

        if data_manager:
            valid_custom_keys = {e.get("key") for e in entries}
            stale_custom_keys = [
                key for key in list(styles.ZEN_THEME.keys())
                if key.startswith("custom_") and key not in valid_custom_keys
            ]
            for key in stale_custom_keys:
                styles.ZEN_THEME.pop(key, None)
                changed = True

        if data_manager and changed:
            self.custom_entries = entries
            self._save_custom_entries()

        return entries

    def _section_label(self, text):
        sep = QWidget()
        lay = QHBoxLayout(sep)
        lay.setContentsMargins(0, 4, 0, 0)
        lay.setSpacing(8)
        line1 = QFrame()
        line1.setFixedHeight(1)
        line1.setFixedWidth(20)
        line1.setStyleSheet(f"background: {self._c['border']};")
        lay.addWidget(line1)
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {self._c['muted_foreground']}; font-size: 9px; font-weight: 700; letter-spacing: 0.1em;"
        )
        lay.addWidget(lbl)
        line2 = QFrame()
        line2.setFixedHeight(1)
        line2.setStyleSheet(f"background: {self._c['border']};")
        lay.addWidget(line2, 1)
        return sep

    def _on_theme_selected(self, theme_key):
        self.themeChosen.emit(styles.resolve_theme_key(theme_key))
        self.close()

    def _build_custom_theme(self):
        dlg = CustomThemeBuilder(dialog_theme=self.current_theme, parent=self)
        dlg.themeBuilt.connect(self._apply_custom_theme)
        dlg.exec()

    def _apply_custom_theme(self, payload):
        if not isinstance(payload, dict):
            return

        if isinstance(payload.get("theme"), dict):
            theme_data = dict(payload["theme"])
            theme_name = str(payload.get("name") or theme_data.get("display_name") or "Custom Theme").strip()
        else:
            theme_data = dict(payload)
            theme_name = str(theme_data.get("display_name") or "Custom Theme").strip()

        if not theme_name:
            theme_name = "Custom Theme"

        key = _make_unique_custom_key(
            theme_name,
            set(styles.ZEN_THEME.keys()).union({entry.get("key", "") for entry in self.custom_entries}),
        )
        theme_data["display_name"] = theme_name
        theme_data.setdefault("display_subtitle", "Custom Theme")
        styles.ZEN_THEME[key] = theme_data

        self.custom_entries.append({"key": key, "name": theme_name, "theme": theme_data})
        self._save_custom_entries()

        self.themeChosen.emit(key)
        self.close()

    def _remove_custom_theme(self):
        if not self.custom_entries:
            return

        target_key = None
        if isinstance(self.current_theme, str) and self.current_theme.startswith("custom_"):
            target_key = self.current_theme
        else:
            target_key = self.custom_entries[-1].get("key")

        if not isinstance(target_key, str) or not target_key:
            return

        styles.ZEN_THEME.pop(target_key, None)
        self.custom_entries = [entry for entry in self.custom_entries if entry.get("key") != target_key]
        self._save_custom_entries()

        fallback = "light" if self.current_theme == target_key else self.current_theme
        self.themeChosen.emit(styles.resolve_theme_key(fallback))
        self.close()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, "_drag_pos"):
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()


class ColorPickerRow(QWidget):
    """One labeled color picker row."""

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
        self.hex_label.setStyleSheet(
            f"color: {c['muted_foreground']}; font-size: 10px; font-family: monospace;"
        )
        layout.addWidget(self.hex_label)
        layout.addStretch()

    def _update_swatch(self):
        self.swatch.setStyleSheet(
            f"QPushButton {{ background: {self.color}; border: 1px solid rgba(128,128,128,0.3); border-radius: 4px; }}"
        )

    def _pick_color(self):
        color = QColorDialog.getColor(QColor(self.color), self, f"Pick {self.key}")
        if color.isValid():
            self.color = color.name()
            self._update_swatch()
            self.hex_label.setText(self.color)
            self.colorChanged.emit(self.key, self.color)


class CustomThemeBuilder(QDialog):
    """Dialog for building a named custom theme with live preview."""

    themeBuilt = pyqtSignal(dict)

    def __init__(self, dialog_theme="light", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Build Custom Theme")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(500)

        c = styles.ZEN_THEME.get(styles.resolve_theme_key(dialog_theme), styles.ZEN_THEME["light"])
        self._c = c
        self._dialog_theme = styles.resolve_theme_key(dialog_theme)
        self._colors = dict(styles.ZEN_THEME.get(self._dialog_theme, styles.ZEN_THEME["light"]))

        container = QWidget()
        container.setObjectName("CustomBuilder")
        container.setStyleSheet(
            f"QWidget#CustomBuilder {{ background: {c['background']}; border: 1px solid {c['border']}; border-radius: 14px; }}"
        )

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

        title = QLabel("Build Your Theme")
        title.setStyleSheet(f"color: {c['foreground']}; font-size: 16px; font-weight: 700;")
        main.addWidget(title)

        sub = QLabel("Pick colors to create your own atmosphere.")
        sub.setStyleSheet(f"color: {c['muted_foreground']}; font-size: 10px; margin-bottom: 4px;")
        main.addWidget(sub)

        name_row = QHBoxLayout()
        name_lbl = QLabel("Theme Name")
        name_lbl.setFixedWidth(110)
        name_lbl.setStyleSheet(f"color: {c['foreground']}; font-size: 11px;")
        name_row.addWidget(name_lbl)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. Ocean Glass")
        self.name_input.setText("My Theme")
        self.name_input.setStyleSheet(
            f"QLineEdit {{ background: {c['card']}; color: {c['foreground']}; border: 1px solid {c['border']}; "
            "border-radius: 6px; padding: 6px 8px; font-size: 11px; }}"
            f"QLineEdit:focus {{ border: 1px solid {c['primary']}; }}"
        )
        name_row.addWidget(self.name_input, 1)
        main.addLayout(name_row)

        preview_row = QHBoxLayout()
        preview_row.setSpacing(10)
        preview_label = QLabel("Preview")
        preview_label.setFixedWidth(110)
        preview_label.setStyleSheet(f"color: {c['foreground']}; font-size: 11px;")
        preview_row.addWidget(preview_label)
        self.preview_widget = ThemePreviewWidget(theme_data=self._colors)
        self.preview_widget.setFixedSize(180, 98)
        preview_row.addWidget(self.preview_widget)
        preview_row.addStretch()
        main.addLayout(preview_row)

        pickers = [
            ("background", "Background", c["background"]),
            ("foreground", "Text Color", c["foreground"]),
            ("primary", "Accent Color", c["primary"]),
            ("card", "Card/Surface", c["card"]),
            ("sidebar_bg", "Sidebar BG", c["sidebar_bg"]),
            ("border", "Border Color", c["border"]),
        ]

        for key, label, default in pickers:
            row = ColorPickerRow(key, label, default, self._dialog_theme)
            row.colorChanged.connect(self._on_color_changed)
            main.addWidget(row)

        main.addSpacing(6)
        footer = QHBoxLayout()
        footer.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet(
            f"QPushButton {{ background: {c['secondary']}; color: {c['foreground']}; border: 1px solid {c['border']}; "
            "border-radius: 6px; padding: 6px 16px; font-size: 11px; }}"
            f"QPushButton:hover {{ background: {c['accent']}; }}"
        )
        cancel_btn.clicked.connect(self.close)
        footer.addWidget(cancel_btn)

        apply_btn = QPushButton("Apply Theme")
        apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        apply_btn.setStyleSheet(
            f"QPushButton {{ background: {c['primary']}; color: {c['primary_foreground']}; border: none; border-radius: 6px; "
            "padding: 6px 20px; font-size: 11px; font-weight: 600; }}"
            "QPushButton:hover { opacity: 0.9; }"
        )
        apply_btn.clicked.connect(self._apply)
        footer.addWidget(apply_btn)
        main.addLayout(footer)

    def _on_color_changed(self, key, hex_color):
        self._colors[key] = hex_color
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
            self._colors["primary_foreground"] = "#FFFFFF"
            qc = QColor(hex_color)
            self._colors["accent"] = f"rgba({qc.red()}, {qc.green()}, {qc.blue()}, 0.12)"
            self._colors["active_item_bg"] = f"rgba({qc.red()}, {qc.green()}, {qc.blue()}, 0.15)"
            self._colors["selection_bg"] = hex_color
            self._colors["primary_gradient"] = (
                f"qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {hex_color}, stop:1 {hex_color}CC)"
            )
            self._colors["primary_gradient_hover"] = (
                f"qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {hex_color}EE, stop:1 {hex_color})"
            )
        elif key == "card":
            self._colors["popover"] = hex_color
            self._colors["input"] = hex_color
            self._colors["elevated"] = hex_color
        elif key == "sidebar_bg":
            self._colors["sidebar_border"] = hex_color
        elif key == "border":
            self._colors["sidebar_border"] = hex_color
        self._colors["preview_gradient"] = [
            self._colors.get("background", "#FFFFFF"),
            self._colors.get("card", "#FFFFFF"),
            self._colors.get("sidebar_bg", "#F3F4F6"),
        ]
        self.preview_widget.set_theme_data(self._colors)

    def _apply(self):
        theme_name = self.name_input.text().strip()
        if not theme_name:
            QMessageBox.warning(self, "Theme Name Required", "Please enter a name for your custom theme.")
            self.name_input.setFocus()
            return

        base = dict(styles.ZEN_THEME.get(self._dialog_theme, styles.ZEN_THEME["light"]))
        base.update(self._colors)
        base["is_dark"] = styles.is_dark_theme(self._dialog_theme)
        base["display_name"] = theme_name
        base["display_subtitle"] = "Custom Theme"
        self.themeBuilt.emit({"name": theme_name, "theme": base})
        self.close()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, "_drag_pos"):
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
