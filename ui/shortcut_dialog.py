from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, 
    QPushButton, QLabel, QHeaderView, QMessageBox, QDialogButtonBox, QWidget
)
from PyQt6.QtGui import QKeySequence, QKeyEvent
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from util.icon_factory import get_premium_icon

class KeyCaptureDialog(QDialog):
    """Small dialog to capture a key sequence."""
    def __init__(self, parent=None, action_name=""):
        super().__init__(parent)
        self.setWindowTitle("Press Keys")
        self.setFixedSize(300, 150)
        self.result_sequence = None
        
        layout = QVBoxLayout(self)
        
        label = QLabel(f"Press combination for:<br><b>{action_name}</b>", self)
        label.setTextFormat(Qt.TextFormat.RichText)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        
        self.key_label = QLabel("...", self)
        self.key_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.key_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #007ACC;")
        layout.addWidget(self.key_label)
        
        note = QLabel("(Press Esc to Cancel, Backspace to Clear)", self)
        note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        note.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(note)

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        modifiers = event.modifiers()
        
        # Ignore standalone modifiers
        if key in (Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt, Qt.Key.Key_Meta):
            return

        # Handle Cancel
        if key == Qt.Key.Key_Escape:
            self.reject()
            return
            
        # Handle Clear
        if key == Qt.Key.Key_Backspace or key == Qt.Key.Key_Delete:
            self.result_sequence = ""
            self.accept()
            return

        # Create Sequence
        # QKeySequence from key event is tricky to match exactly string rep.
        # simpler way: use the int combination
        
        # Construct integer key
        qt_key = key
        # In PyQt6, combining Modifiers with Key for QKeySequence is specific
        # We need to construct the integer value that QKeySequence expects
        
        mod_val = 0
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            mod_val |= Qt.Modifier.CTRL.value
        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            mod_val |= Qt.Modifier.SHIFT.value
        if modifiers & Qt.KeyboardModifier.AltModifier:
            mod_val |= Qt.Modifier.ALT.value
        if modifiers & Qt.KeyboardModifier.MetaModifier:
            mod_val |= Qt.Modifier.META.value
        
        # Combine key int with modifier int
        final_key = qt_key | mod_val
            
        seq = QKeySequence(final_key)
        self.result_sequence = seq.toString()
        self.key_label.setText(self.result_sequence)
        
        # Auto-accept after small delay or immediately?
        # Immediate is better for UX
        self.accept()

class ShortcutDialog(QDialog):
    saved = pyqtSignal() # Emitted when changes are saved

    def __init__(self, shortcut_manager, parent=None):
        super().__init__(parent)
        self.mgr = shortcut_manager
        self.setWindowTitle("Keyboard Shortcuts")
        self.resize(500, 600)
        
        self.layout = QVBoxLayout(self)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Action", "Shortcut", "Edit"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.layout.addWidget(self.table)
        
        # Buttons
        btn_box = QHBoxLayout()
        
        reset_btn = QPushButton("Reset All")
        reset_btn.clicked.connect(self.reset_all)
        btn_box.addWidget(reset_btn)
        
        btn_box.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_box.addWidget(close_btn)
        
        self.layout.addLayout(btn_box)
        
        self.load_data()

    def load_data(self):
        shortcuts = self.mgr.get_all_shortcuts()
        self.table.setRowCount(len(shortcuts))
        
        # Sort by action ID or Description? Description is better.
        sorted_items = sorted(shortcuts.items(), key=lambda x: self.mgr.get_description(x[0]))
        
        for row, (action_id, key_seq) in enumerate(sorted_items):
            desc = self.mgr.get_description(action_id)
            
            # Col 0: Description
            self.table.setItem(row, 0, QTableWidgetItem(desc))
            
            # Col 1: Shortcut
            self.table.setItem(row, 1, QTableWidgetItem(key_seq))
            
            # Col 2: Edit Button
            edit_btn = QPushButton()
            edit_btn.setIcon(get_premium_icon("pencil"))
            edit_btn.setIconSize(QSize(16, 16))
            edit_btn.setFixedSize(30, 25)
            # Use partial or lambda with capture
            edit_btn.clicked.connect(lambda checked, aid=action_id, r=row: self.edit_shortcut(aid, r))
            
            cell_widget = QWidget()
            layout = QHBoxLayout(cell_widget)
            layout.setContentsMargins(0,0,0,0)
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(edit_btn)
            self.table.setCellWidget(row, 2, cell_widget)

    def edit_shortcut(self, action_id, row):
        desc = self.mgr.get_description(action_id)
        capture = KeyCaptureDialog(self, desc)
        if capture.exec() == QDialog.DialogCode.Accepted:
            new_key = capture.result_sequence
            
            # Collision Check
            existing = self.mgr.get_all_shortcuts()
            collision_id = None
            for aid, key in existing.items():
                if aid != action_id and key == new_key and new_key != "":
                    collision_id = aid
                    break
            
            if collision_id:
                coll_desc = self.mgr.get_description(collision_id)
                reply = QMessageBox.question(
                    self, "Collision Detected", 
                    f"The key '{new_key}' is already used by:\n<b>{coll_desc}</b>\n\nOverwrite it?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    # Clear the other one
                    self.mgr.set_shortcut(collision_id, "")
                else:
                    return

            # Proceed
            self.mgr.set_shortcut(action_id, new_key)
            self.mgr._save() # Save immediately
            
            # Reload One Row? Or All?
            # Easiest to reload all to reflect cleared collision
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
