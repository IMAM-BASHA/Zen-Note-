from PyQt6.QtWidgets import QVBoxLayout, QPushButton, QHBoxLayout, QWidget, QLabel
from PyQt6.QtCore import Qt, QSize
from ui.editor import TextEditor
from util.icon_factory import get_premium_icon
from ui.zen_dialog import ZenDialog
import ui.styles as styles

class NoteOverlayDialog(ZenDialog):
    def __init__(self, note_id, note_title, note_content, data_manager, parent=None):
        # Auto-detect theme from parent or data_manager
        theme_mode = "light"
        if parent and hasattr(parent, 'theme_mode'):
            theme_mode = parent.theme_mode
        elif data_manager:
            theme_mode = data_manager.get_setting("theme_mode", "light")
            
        super().__init__(parent, title=note_title, theme_mode=theme_mode)
        self.note_id = note_id
        self.data_manager = data_manager
        self.resize(800, 600)
        
        # Editor
        self.editor = TextEditor(data_manager=self.data_manager)
        self.editor.editor.setHtml(note_content)
        self.editor.set_theme_mode(theme_mode)
        
        # Handle links inside overlay
        if self.parent() and hasattr(self.parent(), 'open_note_by_id'):
            self.editor.request_open_note.connect(self.parent().open_note_by_id)
            
        if self.parent() and hasattr(self.parent(), 'open_note_overlay'):
             self.editor.request_open_note_overlay.connect(self.parent().open_note_overlay)
        
        self.content_layout.addWidget(self.editor)
        
    def apply_theme(self, mode):
        """Standard theme application (ZenDialog base handles most)."""
        super().apply_theme(mode) # Updates header/container
        if hasattr(self, 'editor'):
            self.editor.set_theme_mode(mode)
            
    def closeEvent(self, event):
        # Save on close?
        # For now, just close. If editable, we might want to save.
        super().closeEvent(event)
