from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, 
    QPushButton, QLabel, QHeaderView, QMessageBox, QWidget
)
from PyQt6.QtGui import QKeySequence, QKeyEvent
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from util.icon_factory import get_premium_icon
import ui.styles as styles
from ui.zen_dialog import ZenDialog

class KeyCaptureDialog(ZenDialog):
    """Small dialog to capture a key sequence."""
    def __init__(self, parent=None, action_name="", theme_mode="light"):
        super().__init__(parent, title="Press Keys", theme_mode=theme_mode)
        self.setFixedSize(300, 180)
        self.result_sequence = None
        
        label = QLabel(f"Press combination for:<br><b>{action_name}</b>")
        label.setTextFormat(Qt.TextFormat.RichText)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(label)
        
        self.key_label = QLabel("...")
        self.key_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(self.key_label)
        
        note = QLabel("(Press Esc to Cancel, Backspace to Clear)")
        note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        note.setStyleSheet("font-size: 11px; opacity: 0.7;")
        self.content_layout.addWidget(note)
        
        self._apply_theme_local()

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        modifiers = event.modifiers()
        
        if key in (Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt, Qt.Key.Key_Meta):
            return

        if key == Qt.Key.Key_Escape:
            self.reject()
            return
            
        if key == Qt.Key.Key_Backspace or key == Qt.Key.Key_Delete:
            self.result_sequence = ""
            self.accept()
            return
        
        mod_val = 0
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            mod_val |= Qt.Modifier.CTRL.value
        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            mod_val |= Qt.Modifier.SHIFT.value
        if modifiers & Qt.KeyboardModifier.AltModifier:
            mod_val |= Qt.Modifier.ALT.value
        if modifiers & Qt.KeyboardModifier.MetaModifier:
            mod_val |= Qt.Modifier.META.value
        
        final_key = key | mod_val
        seq = QKeySequence(final_key)
        self.result_sequence = seq.toString()
        self.key_label.setText(self.result_sequence)
        self.accept()

    def _apply_theme_local(self):
        c = styles.ZEN_THEME.get(self.theme_mode, styles.ZEN_THEME["light"])
        accent = c['primary']
        self.key_label.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {accent}; margin-top: 10px;")

class ShortcutDialog(ZenDialog):
    saved = pyqtSignal()

    def __init__(self, shortcut_manager, parent=None):
        # Auto-detect theme
        theme_mode = "light"
        if parent and hasattr(parent, 'theme_mode'):
            theme_mode = parent.theme_mode
        elif parent and hasattr(parent, 'data_manager'):
            theme_mode = parent.data_manager.get_setting("theme_mode", "light")
            
        super().__init__(parent, title="Keyboard Shortcuts", theme_mode=theme_mode)
        self.mgr = shortcut_manager
        self.resize(550, 650)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Action", "Shortcut", "Edit"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.content_layout.addWidget(self.table)
        
        # Buttons
        btn_box = QHBoxLayout()
        
        reset_btn = QPushButton("Reset All")
        reset_btn.clicked.connect(self.reset_all)
        btn_box.addWidget(reset_btn)
        
        btn_box.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        close_btn.setDefault(True)
        btn_box.addWidget(close_btn)
        
        self.content_layout.addLayout(btn_box)
        
        self.apply_theme_local()
        self.load_data()

    def load_data(self):
        shortcuts = self.mgr.get_all_shortcuts()
        self.table.setRowCount(len(shortcuts))
        sorted_items = sorted(shortcuts.items(), key=lambda x: self.mgr.get_description(x[0]))
        
        for row, (action_id, key_seq) in enumerate(sorted_items):
            desc = self.mgr.get_description(action_id)
            self.table.setItem(row, 0, QTableWidgetItem(desc))
            self.table.setItem(row, 1, QTableWidgetItem(key_seq))
            
            edit_btn = QPushButton()
            edit_btn.setIcon(get_premium_icon("pencil"))
            edit_btn.setIconSize(QSize(16, 16))
            edit_btn.setFixedSize(30, 25)
            edit_btn.clicked.connect(lambda checked, aid=action_id, r=row: self.edit_shortcut(aid, r))
            
            cell_widget = QWidget()
            layout = QHBoxLayout(cell_widget)
            layout.setContentsMargins(0,0,0,0)
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(edit_btn)
            self.table.setCellWidget(row, 2, cell_widget)

    def edit_shortcut(self, action_id, row):
        desc = self.mgr.get_description(action_id)
        capture = KeyCaptureDialog(self, desc, self.theme_mode)
        if capture.exec() == QDialog.DialogCode.Accepted:
            new_key = capture.result_sequence
            
            existing = self.mgr.get_all_shortcuts()
            collision_id = None
            for aid, key in existing.items():
                if aid != action_id and key == new_key and new_key != "":
                    collision_id = aid
                    break
            
            if collision_id:
                coll_desc = self.mgr.get_description(collision_id)
                # Note: QMessageBox still uses OS style for now, but we've fixed the custom ones.
                reply = QMessageBox.question(
                    self, "Collision Detected", 
                    f"The key '{new_key}' is already used by:\n<b>{coll_desc}</b>\n\nOverwrite it?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.mgr.set_shortcut(collision_id, "")
                else:
                    return

            self.mgr.set_shortcut(action_id, new_key)
            self.mgr._save()
            self.load_data()
            self.saved.emit()

    def reset_all(self):
        confirm = QMessageBox.question(
            self, "Reset Shortcuts",
            "Reset all shortcuts to default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.mgr.reset_all()
            self.load_data()
            self.saved.emit()

    def apply_theme_local(self):
        c = styles.ZEN_THEME.get(self.theme_mode, styles.ZEN_THEME["light"])
        
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {c['background']};
                color: {c['foreground']};
                border: 1px solid {c['border']};
                border-radius: 8px;
                gridline-color: {c['border']};
                padding: 5px;
            }}
            QHeaderView::section {{
                background-color: {c['muted']};
                color: {c['muted_foreground']};
                border: none;
                padding: 6px;
                font-weight: bold;
            }}
            QTableWidget::item {{
                padding: 6px;
                border-bottom: 1px solid {c['border']};
            }}
            QTableWidget::item:selected {{
                background-color: {c['active_item_bg']};
                color: {c['primary']};
            }}
        """)
        
        btn_style = f"""
            QPushButton {{
                background-color: {c['secondary']};
                color: {c['foreground']};
                border: 1px solid {c['border']};
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {c['accent']};
            }}
        """
        self.setStyleSheet(self.styleSheet() + btn_style)
