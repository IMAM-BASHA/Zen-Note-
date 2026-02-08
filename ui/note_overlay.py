from PyQt6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QHBoxLayout, QWidget, QLabel
from PyQt6.QtCore import Qt, QSize
from ui.editor import TextEditor
from util.icon_factory import get_premium_icon

class NoteOverlayDialog(QDialog):
    def __init__(self, note_id, note_title, note_content, data_manager, parent=None):
        super().__init__(parent)
        self.note_id = note_id
        self.data_manager = data_manager
        self.setWindowTitle(note_title)
        self.resize(600, 400)
        
        # Window Flags for Overlay feel (Always on top? Optional, maybe just a dialog)
        # self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowFlags(Qt.WindowType.Window) # Independent window
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QWidget()
        header.setStyleSheet("background-color: #f5f5f5; border-bottom: 1px solid #ddd;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 5, 10, 5)
        
        title_lbl = QLabel(note_title)
        title_lbl.setStyleSheet("font-weight: bold; font-size: 14px; color: #333;")
        header_layout.addWidget(title_lbl)
        header_layout.addStretch()
        
        # Close Button
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.close)
        header_layout.addWidget(btn_close)
        
        layout.addWidget(header)
        
        # Editor
        self.editor = TextEditor(data_manager=self.data_manager)
        self.editor.editor.setHtml(note_content)
        
        # Apply Theme (Detect from parent or data_manager)
        current_theme = self.data_manager.get_setting("theme_mode", "light")
        self.editor.set_theme_mode(current_theme)
        
        # Handle links inside overlay
        if self.parent() and hasattr(self.parent(), 'open_note_by_id'):
            self.editor.request_open_note.connect(self.parent().open_note_by_id)
            
        if self.parent() and hasattr(self.parent(), 'open_note_overlay'):
             self.editor.request_open_note_overlay.connect(self.parent().open_note_overlay)
        
        layout.addWidget(self.editor)
        
    def closeEvent(self, event):
        # Save on close?
        # For now, just close. If editable, we might want to save.
        pass
