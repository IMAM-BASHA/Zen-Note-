"""
Focus Mode Dialog — Ambient Soundscapes
A premium dialog for focus mode with ambient sound playback.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QWidget, QGraphicsDropShadowEffect, QSizePolicy, QSlider,
    QFileDialog, QLineEdit, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QUrl, QTimer
from PyQt6.QtGui import QColor, QFont, QIcon
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
import ui.styles as styles
import json
import os

SETTINGS_FILE = "focus_mode_settings.json"

# Preset ambient sounds with emoji icons
PRESET_SOUNDS = [
    {"key": "rain",   "name": "Heavy Rain",   "icon": "🌧️", "url": ""},
    {"key": "forest", "name": "Deep Forest",  "icon": "🌲", "url": ""},
    {"key": "white",  "name": "White Noise",  "icon": "🎛️", "url": ""},
    {"key": "ocean",  "name": "Ocean Waves",  "icon": "🌊", "url": ""},
    {"key": "fire",   "name": "Fireplace",    "icon": "🔥", "url": ""},
    {"key": "cafe",   "name": "Café Ambience", "icon": "☕", "url": ""},
]


class SoundCard(QWidget):
    """A selectable ambient sound card."""
    selected = pyqtSignal(str)  # Emits the sound key
    
    def __init__(self, sound_data, is_active=False, theme_colors=None, parent=None):
        super().__init__(parent)
        self.sound_key = sound_data["key"]
        self.sound_name = sound_data["name"]
        self.sound_icon = sound_data["icon"]
        self.is_active = is_active
        c = theme_colors or styles.ZEN_THEME["dark"]
        
        self.setFixedSize(110, 100)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 12, 8, 8)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Icon
        icon_label = QLabel(self.sound_icon)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("font-size: 28px; background: transparent;")
        layout.addWidget(icon_label)
        
        # Name
        name_label = QLabel(self.sound_name)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setWordWrap(True)
        name_label.setStyleSheet(f"""
            color: {c['foreground']};
            font-size: 11px;
            font-weight: 500;
            background: transparent;
        """)
        layout.addWidget(name_label)
        
        self._apply_style(c)
    
    def _apply_style(self, c):
        if self.is_active:
            self.setStyleSheet(f"""
                SoundCard {{
                    background-color: {c['accent']};
                    border: 2px solid {c['primary']};
                    border-radius: 12px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                SoundCard {{
                    background-color: {c['card']};
                    border: 1px solid {c['border']};
                    border-radius: 12px;
                }}
                SoundCard:hover {{
                    border-color: {c['primary']};
                }}
            """)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.selected.emit(self.sound_key)


class CustomSoundItem(QWidget):
    """A single custom sound entry with remove button."""
    removeRequested = pyqtSignal(int)
    playRequested = pyqtSignal(str)  # Emits the path/URL
    
    def __init__(self, index, name, path, theme_colors=None, parent=None):
        super().__init__(parent)
        self.index = index
        self.path = path
        c = theme_colors or styles.ZEN_THEME["dark"]
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(8)
        
        # Play button
        play_btn = QPushButton("▶")
        play_btn.setFixedSize(28, 28)
        play_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        play_btn.setStyleSheet(f"""
            QPushButton {{
                background: {c['primary']};
                color: {c['primary_foreground']};
                border: none;
                border-radius: 14px;
                font-size: 12px;
            }}
            QPushButton:hover {{ background: {c['ring']}; }}
        """)
        play_btn.clicked.connect(lambda: self.playRequested.emit(self.path))
        layout.addWidget(play_btn)
        
        # Info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(0)
        
        name_lbl = QLabel(name)
        name_lbl.setStyleSheet(f"color: {c['foreground']}; font-size: 12px; font-weight: 600;")
        info_layout.addWidget(name_lbl)
        
        path_lbl = QLabel(path if len(path) < 40 else "..." + path[-37:])
        path_lbl.setStyleSheet(f"color: {c['muted_foreground']}; font-size: 10px;")
        info_layout.addWidget(path_lbl)
        layout.addLayout(info_layout, 1)
        
        # Remove
        rm_btn = QPushButton("✕")
        rm_btn.setFixedSize(22, 22)
        rm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        rm_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {c['muted_foreground']};
                border: none;
                border-radius: 11px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background: {c['destructive']};
                color: white;
            }}
        """)
        rm_btn.clicked.connect(lambda: self.removeRequested.emit(self.index))
        layout.addWidget(rm_btn)
        
        self.setStyleSheet(f"""
            CustomSoundItem {{
                background-color: {c['card']};
                border: 1px solid {c['border']};
                border-radius: 8px;
            }}
        """)


class FocusModeDialog(QDialog):
    """Premium Focus Mode dialog with ambient soundscapes."""
    
    def __init__(self, current_theme="light", data_manager=None, parent=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self.current_theme = current_theme
        self.c = styles.ZEN_THEME.get(current_theme, styles.ZEN_THEME["light"])
        self._active_sound = None
        self._custom_sounds = []
        self._load_settings()
        
        # Audio
        self._player = QMediaPlayer()
        self._audio_output = QAudioOutput()
        self._player.setAudioOutput(self._audio_output)
        self._audio_output.setVolume(0.5)
        
        self.setWindowTitle("Focus Mode")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumWidth(520)
        self.setMaximumWidth(600)
        
        # Main container
        container = QWidget()
        container.setObjectName("FocusModeContainer")
        container.setStyleSheet(f"""
            QWidget#FocusModeContainer {{
                background-color: {self.c['background']};
                border: 1px solid {self.c['border']};
                border-radius: 16px;
            }}
        """)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 80))
        container.setGraphicsEffect(shadow)
        
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.addWidget(container)
        
        main = QVBoxLayout(container)
        main.setContentsMargins(28, 24, 28, 24)
        main.setSpacing(16)
        
        # ── Header ──
        header = QHBoxLayout()
        title_col = QVBoxLayout()
        title_col.setSpacing(4)
        
        title = QLabel("Focus Mode")
        title.setStyleSheet(f"""
            color: {self.c['foreground']};
            font-size: 22px;
            font-weight: 700;
        """)
        title_col.addWidget(title)
        
        subtitle = QLabel("Customize your distraction-free environment for deep work.")
        subtitle.setStyleSheet(f"color: {self.c['muted_foreground']}; font-size: 12px;")
        title_col.addWidget(subtitle)
        
        header.addLayout(title_col, 1)
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {self.c['muted_foreground']};
                border: none; font-size: 16px; border-radius: 14px;
            }}
            QPushButton:hover {{
                background: {self.c['accent']};
                color: {self.c['foreground']};
            }}
        """)
        close_btn.clicked.connect(self.close)
        header.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignTop)
        main.addLayout(header)
        
        # ── Section: Ambient Soundscapes ──
        main.addWidget(self._section_label("AMBIENT SOUNDSCAPES"))
        
        # Sound cards grid (3 per row)
        row1 = QHBoxLayout()
        row1.setSpacing(10)
        row2 = QHBoxLayout()
        row2.setSpacing(10)
        
        for i, snd in enumerate(PRESET_SOUNDS):
            card = SoundCard(snd, is_active=(snd["key"] == self._active_sound), theme_colors=self.c)
            card.selected.connect(self._on_preset_selected)
            if i < 3:
                row1.addWidget(card)
            else:
                row2.addWidget(card)
        
        # Fill remainder to balance layout
        row1.addStretch()
        row2.addStretch()
        
        main.addLayout(row1)
        main.addLayout(row2)
        
        # Volume slider
        vol_row = QHBoxLayout()
        vol_row.setSpacing(8)
        vol_icon = QLabel("🔊")
        vol_icon.setStyleSheet("font-size: 16px;")
        vol_row.addWidget(vol_icon)
        
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                background: {self.c['secondary']};
                height: 6px;
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {self.c['primary']};
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }}
            QSlider::sub-page:horizontal {{
                background: {self.c['primary']};
                border-radius: 3px;
            }}
        """)
        self.volume_slider.valueChanged.connect(self._on_volume_changed)
        vol_row.addWidget(self.volume_slider, 1)
        
        self.vol_label = QLabel("50%")
        self.vol_label.setFixedWidth(35)
        self.vol_label.setStyleSheet(f"color: {self.c['muted_foreground']}; font-size: 11px;")
        vol_row.addWidget(self.vol_label)
        main.addLayout(vol_row)
        
        # ── Section: Your Sounds ──
        main.addWidget(self._section_label("YOUR SOUNDS"))
        
        # Custom sounds list
        self.custom_sounds_container = QVBoxLayout()
        self.custom_sounds_container.setSpacing(6)
        self._rebuild_custom_list()
        main.addLayout(self.custom_sounds_container)
        
        # Add sound buttons
        add_row = QHBoxLayout()
        add_row.setSpacing(8)
        
        add_local_btn = QPushButton("📂 Add Local File")
        add_local_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_local_btn.setStyleSheet(self._action_btn_style())
        add_local_btn.clicked.connect(self._add_local_sound)
        add_row.addWidget(add_local_btn)
        
        add_yt_btn = QPushButton("🔗 Add YouTube URL")
        add_yt_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_yt_btn.setStyleSheet(self._action_btn_style())
        add_yt_btn.clicked.connect(self._add_youtube_sound)
        add_row.addWidget(add_yt_btn)
        
        add_row.addStretch()
        main.addLayout(add_row)
        
        # ── Footer ──
        main.addSpacing(8)
        footer = QHBoxLayout()
        footer.addStretch()
        
        # Stop button
        stop_btn = QPushButton("⏹ Stop Sound")
        stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        stop_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.c['secondary']};
                color: {self.c['foreground']};
                border: 1px solid {self.c['border']};
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 500;
                font-size: 12px;
            }}
            QPushButton:hover {{ background: {self.c['accent']}; }}
        """)
        stop_btn.clicked.connect(self._stop_sound)
        footer.addWidget(stop_btn)
        
        close_footer = QPushButton("Close")
        close_footer.setCursor(Qt.CursorShape.PointingHandCursor)
        close_footer.setStyleSheet(f"""
            QPushButton {{
                background: {self.c['primary']};
                color: {self.c['primary_foreground']};
                border: none;
                border-radius: 8px;
                padding: 8px 20px;
                font-weight: 600;
                font-size: 12px;
            }}
            QPushButton:hover {{ opacity: 0.9; }}
        """)
        close_footer.clicked.connect(self.close)
        footer.addWidget(close_footer)
        main.addLayout(footer)
    
    # ── Helpers ──
    
    def _section_label(self, text):
        sep = QWidget()
        sep_layout = QHBoxLayout(sep)
        sep_layout.setContentsMargins(0, 4, 0, 0)
        sep_layout.setSpacing(8)
        
        line_left = QFrame()
        line_left.setFixedHeight(1)
        line_left.setFixedWidth(20)
        line_left.setStyleSheet(f"background: {self.c['border']};")
        sep_layout.addWidget(line_left)
        
        lbl = QLabel(text)
        lbl.setStyleSheet(f"""
            color: {self.c['muted_foreground']};
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 0.1em;
        """)
        sep_layout.addWidget(lbl)
        
        line_right = QFrame()
        line_right.setFixedHeight(1)
        line_right.setStyleSheet(f"background: {self.c['border']};")
        sep_layout.addWidget(line_right, 1)
        
        return sep
    
    def _action_btn_style(self):
        return f"""
            QPushButton {{
                background: {self.c['card']};
                color: {self.c['foreground']};
                border: 1px dashed {self.c['border']};
                border-radius: 8px;
                padding: 8px 14px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                border-color: {self.c['primary']};
                background: {self.c['accent']};
            }}
        """
    
    def _rebuild_custom_list(self):
        # Clear
        while self.custom_sounds_container.count():
            item = self.custom_sounds_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not self._custom_sounds:
            empty = QLabel("No custom sounds added yet.")
            empty.setStyleSheet(f"color: {self.c['muted_foreground']}; font-size: 11px; padding: 8px;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.custom_sounds_container.addWidget(empty)
        else:
            for i, snd in enumerate(self._custom_sounds):
                item = CustomSoundItem(i, snd.get("name", "Custom"), snd.get("path", ""), theme_colors=self.c)
                item.removeRequested.connect(self._remove_custom_sound)
                item.playRequested.connect(self._play_custom_sound)
                self.custom_sounds_container.addWidget(item)
    
    # ── Actions ──
    
    def _on_preset_selected(self, key):
        self._active_sound = key
        self._save_settings()
        # For presets without bundled files, show info
        # In production, these would be actual audio files
        self.close()
        self._reopen()
    
    def _reopen(self):
        """Reopen the dialog to refresh card states."""
        dlg = FocusModeDialog(self.current_theme, self.data_manager, self.parent())
        dlg.exec()
    
    def _on_volume_changed(self, value):
        self._audio_output.setVolume(value / 100.0)
        self.vol_label.setText(f"{value}%")
    
    def _stop_sound(self):
        self._player.stop()
        self._active_sound = None
        self._save_settings()
    
    def _add_local_sound(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Audio File", "",
            "Audio Files (*.mp3 *.wav *.ogg *.flac *.m4a);;All Files (*)"
        )
        if path:
            name = os.path.basename(path)
            self._custom_sounds.append({"name": name, "path": path, "type": "local"})
            self._save_settings()
            self._rebuild_custom_list()
    
    def _add_youtube_sound(self):
        """Show an inline input for YouTube URL."""
        from ui.zen_dialog import ZenInputDialog
        text, ok = ZenInputDialog.getText(
            self, "YouTube Sound", "Paste YouTube URL:",
            theme_mode=self.current_theme
        )
        if ok and text.strip():
            url = text.strip()
            # Extract a simple name from URL
            name = "YouTube Sound"
            if "v=" in url:
                name = f"YouTube: {url.split('v=')[-1][:11]}"
            elif "youtu.be/" in url:
                name = f"YouTube: {url.split('/')[-1][:11]}"
            self._custom_sounds.append({"name": name, "path": url, "type": "youtube"})
            self._save_settings()
            self._rebuild_custom_list()
    
    def _play_custom_sound(self, path):
        """Play a custom sound file or open YouTube URL."""
        if path.startswith("http"):
            import webbrowser
            webbrowser.open(path)
        else:
            self._player.setSource(QUrl.fromLocalFile(path))
            self._player.setLoops(QMediaPlayer.Loops.Infinite)
            self._player.play()
    
    def _remove_custom_sound(self, index):
        if 0 <= index < len(self._custom_sounds):
            self._custom_sounds.pop(index)
            self._save_settings()
            self._rebuild_custom_list()
    
    # ── Persistence ──
    
    def _load_settings(self):
        try:
            if self.data_manager:
                data = self.data_manager.get_setting("focus_mode", {})
                if isinstance(data, str):
                    data = json.loads(data)
                self._active_sound = data.get("active_sound")
                self._custom_sounds = data.get("custom_sounds", [])
            elif os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, "r") as f:
                    data = json.load(f)
                    self._active_sound = data.get("active_sound")
                    self._custom_sounds = data.get("custom_sounds", [])
        except Exception:
            self._active_sound = None
            self._custom_sounds = []
    
    def _save_settings(self):
        data = {
            "active_sound": self._active_sound,
            "custom_sounds": self._custom_sounds,
        }
        try:
            if self.data_manager:
                self.data_manager.set_setting("focus_mode", data)
            else:
                with open(SETTINGS_FILE, "w") as f:
                    json.dump(data, f)
        except Exception:
            pass
    
    # ── Dragging ──
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, '_drag_pos'):
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
