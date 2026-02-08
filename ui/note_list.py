from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, QLabel, QPushButton, QLineEdit, QApplication, QColorDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from ui.color_delegate import ColorDelegate, COLOR_ROLE
from util.icon_factory import get_premium_icon, get_combined_indicators

class NoteList(QWidget):
    noteSelected = pyqtSignal(str)
    createNoteRequest = pyqtSignal()
    deleteNote = pyqtSignal(str)
    renameNote = pyqtSignal(str, str)
    updateNote = pyqtSignal(str, dict)  # Emit note_id, updates dict (e.g. {'is_pinned': True})
    insertNoteAtPosition = pyqtSignal(int)
    reorderNote = pyqtSignal(str, int)
    moveNoteToFolder = pyqtSignal(str)   # Emit note_id when user wants to move note
    exportNote = pyqtSignal(str)         # Emit note_id for export
    previewNote = pyqtSignal(str)        # Emit note_id for preview

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("NoteList")
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        self.wrap_enabled = False
        self.showing_archived = False
        self.current_notes = []
        self.theme_mode = "light"
        
        self._setup_top_controls()
        self._setup_search()
        self._setup_list()
        
    def _setup_top_controls(self):
        top_container = QWidget()
        top_layout = QVBoxLayout(top_container)
        top_layout.setContentsMargins(10, 10, 10, 5)
        
        # Back Button (Hidden by default)
        self.back_btn = QPushButton(" Back to Notes")
        self.back_btn.setIcon(get_premium_icon("back"))
        self.back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_btn.clicked.connect(self.toggle_archived_view)
        self.back_btn.setVisible(False)
        top_layout.addWidget(self.back_btn)

        self.new_note_btn = QPushButton(" New Note")
        self.new_note_btn.setIcon(get_premium_icon("plus", color="white"))
        self.new_note_btn.setObjectName("NewNoteBtn")
        self.new_note_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.new_note_btn.clicked.connect(self.createNoteRequest.emit)
        top_layout.addWidget(self.new_note_btn)
        
        self.layout.addWidget(top_container)
        
    def _setup_search(self):
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search title & content...")
        self.search_input.setObjectName("SearchInput")
        self.search_input.textChanged.connect(self.filter_notes)
        self.layout.addWidget(self.search_input)
        
    def _setup_list(self):
        self.list_widget = QListWidget()
        self.list_widget.setObjectName("NoteItems")
        self.list_widget.setIconSize(QSize(48, 16)) # Space for 3 icons
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        self.list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)
        self.list_widget.setItemDelegate(ColorDelegate(self.list_widget))
        
        self.list_widget.setResizeMode(QListWidget.ResizeMode.Adjust)
        
        self.list_widget.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.list_widget.model().rowsMoved.connect(self.on_rows_moved)
        
        self.list_widget.setDragEnabled(True)
        self.list_widget.setDropIndicatorShown(True)
        
        self.layout.addWidget(self.list_widget)
        
    def set_wrap_mode(self, enabled):
        self.wrap_enabled = enabled
        self.list_widget.setWordWrap(enabled)
        # Force a viewport update to trigger sizeHint recalculation
        self.list_widget.viewport().update()
        self.filter_notes(self.search_input.text())
        
    def load_notes(self, notes):
        self.current_notes = notes
        self.filter_notes(self.search_input.text())
        
    def filter_notes(self, text):
        from PyQt6.QtGui import QTextDocument
        from PyQt6.QtWidgets import QListWidgetItem
        
        self.list_widget.clear()
        text = text.lower().strip()
        
        # Disable drag-and-drop if filtering
        is_filtered = bool(text)
        if is_filtered:
            self.list_widget.setDragDropMode(QListWidget.DragDropMode.NoDragDrop)
        else:
            self.list_widget.setDragDropMode(QListWidget.DragDropMode.InternalMove)

        doc = QTextDocument()
        filtered_notes = []
        for note in self.current_notes:
            try:
                if self.showing_archived:
                    if not getattr(note, 'is_archived', False): continue
                else:
                    if getattr(note, 'is_archived', False): continue

                note_title = str(note.title) if note.title else "Untitled"
                title_match = text in note_title.lower()
                
                content_match = False
                if not title_match and note.content and is_filtered:
                    try:
                        doc.setHtml(note.content)
                        plain_text = doc.toPlainText().lower()
                        content_match = text in plain_text
                    except: content_match = False
                
                if title_match or content_match or not is_filtered:
                    filtered_notes.append(note)
            except Exception: continue

        def sort_key(n):
            pinned_rank = not getattr(n, 'is_pinned', False)
            p = getattr(n, 'priority', 0)
            priority_rank = p if p > 0 else 999
            order_rank = getattr(n, 'order', 0)
            return (pinned_rank, priority_rank, order_rank)

        filtered_notes.sort(key=sort_key)

        if not self.showing_archived and not text:
            archived_count = sum(1 for n in self.current_notes if getattr(n, 'is_archived', False))
            if archived_count > 0:
                icon_color = "white" if self.theme_mode == "dark" else None
                archived_item = QListWidgetItem(f" Archived Notes ({archived_count})")
                archived_item.setIcon(get_premium_icon("folder_archived", color=icon_color))
                archived_item.setData(Qt.ItemDataRole.UserRole, "ARCHIVED_ROOT")
                font = archived_item.font()
                font.setBold(True)
                archived_item.setFont(font)
                self.list_widget.addItem(archived_item)

        for idx, note in enumerate(filtered_notes, 1):
            try:
                note_title = str(note.title) if note.title else "Untitled"
                prefix = ""
                p = getattr(note, 'priority', 0)
                if p == 1: prefix += "❶ "
                elif p == 2: prefix += "❷ "
                elif p == 3: prefix += "❸ "
                
                # Combine Indicators
                indicators = ["list"]
                if getattr(note, 'is_pinned', False): indicators.append("pin")
                if getattr(note, 'is_locked', False): indicators.append("lock")
                
                item = QListWidgetItem(f"{idx}. {prefix}{note_title}")
                icon_color = "white" if self.theme_mode == "dark" else None
                item.setIcon(get_combined_indicators(indicators, color=icon_color))
                item.setData(Qt.ItemDataRole.UserRole, note.id)
                if getattr(note, 'color', None):
                    item.setData(COLOR_ROLE, note.color)
                self.list_widget.addItem(item)
            except Exception: continue
        
    def on_item_clicked(self, item):
        note_id = item.data(Qt.ItemDataRole.UserRole)
        print(f"DEBUG: NoteList.on_item_clicked: note_id='{note_id}'")
        if note_id == "ARCHIVED_ROOT":
            self.toggle_archived_view()
        else:
            print(f"DEBUG: NoteList EMITTING noteSelected('{note_id}')")
            self.noteSelected.emit(note_id)
        
    def on_rows_moved(self, parent, start, end, dest_parent, dest_row):
        new_position = dest_row - 1 if dest_row > start else dest_row
        item = self.list_widget.item(new_position)
        if item:
            note_id = item.data(Qt.ItemDataRole.UserRole)
            self.reorderNote.emit(note_id, new_position)
            
    def on_notebook_changed(self):
        self.filter_notes(self.search_input.text())

    def set_theme_mode(self, mode):
        """Refreshes icons for theme changes."""
        self.theme_mode = mode
        is_dark = mode == "dark"
        icon_color = "#FFFFFF" if is_dark else "#09090b"
        
        self.back_btn.setIcon(get_premium_icon("back", color=icon_color))
        self.filter_notes(self.search_input.text())
        
    def show_context_menu(self, pos):
        item = self.list_widget.itemAt(pos)
        if not item: return
        from PyQt6.QtWidgets import QMenu, QMessageBox, QInputDialog
        menu = QMenu()
        note_id = item.data(Qt.ItemDataRole.UserRole)
        note = next((n for n in self.current_notes if n.id == note_id), None)
        if not note: return
        
        pin_text = "Unpin Note" if getattr(note, 'is_pinned', False) else "Pin Note"
        pin_action = menu.addAction(pin_text)
        
        prio_menu = menu.addMenu("Set Priority")
        current_prio = getattr(note, 'priority', 0)
        p1 = prio_menu.addAction("❶ High (1)"); p1.setCheckable(True); p1.setChecked(current_prio == 1)
        p2 = prio_menu.addAction("❷ Medium (2)"); p2.setCheckable(True); p2.setChecked(current_prio == 2)
        p3 = prio_menu.addAction("❸ Low (3)"); p3.setCheckable(True); p3.setChecked(current_prio == 3)
        pn = prio_menu.addAction("None"); pn.setCheckable(True); pn.setChecked(current_prio == 0)
        
        menu.addSeparator()
        color_action = menu.addAction("🎨 Set Color...")
        lock_text = "Unlock Note" if getattr(note, 'is_locked', False) else "Lock Note"
        lock_action = menu.addAction(lock_text)

        menu.addSeparator()
        rename_action = menu.addAction("Rename Note")
        if getattr(note, 'is_locked', False):
            rename_action.setEnabled(False)
            delete_action = menu.addAction("Delete Note (Locked)"); delete_action.setEnabled(False)
        else:
            delete_action = menu.addAction("Delete Note")
        
        move_action = menu.addAction("Move to Notebook")
        preview_action = menu.addAction("Preview Note PDF")
        export_action = menu.addAction("Export to PDF")
        
        menu.addSeparator()
        archive_action = menu.addAction("Unarchive" if getattr(note, 'is_archived', False) else "Archive")
        
        action = menu.exec(self.list_widget.mapToGlobal(pos))
        
        if action == pin_action: self.updateNote.emit(note_id, {"is_pinned": not getattr(note, 'is_pinned', False)})
        elif action == color_action:
            from PyQt6.QtGui import QColor
            initial_color = getattr(note, 'color', '#FFFFFF') or '#FFFFFF'
            initial = QColor(initial_color)
            color = QColorDialog.getColor(initial, self, "Select Note Color")
            if color.isValid(): self.updateNote.emit(note_id, {"color": color.name()})
        elif action == lock_action: self.updateNote.emit(note_id, {"is_locked": not getattr(note, 'is_locked', False)})
        elif action == p1: self.updateNote.emit(note_id, {"priority": 1})
        elif action == p2: self.updateNote.emit(note_id, {"priority": 2})
        elif action == p3: self.updateNote.emit(note_id, {"priority": 3})
        elif action == pn: self.updateNote.emit(note_id, {"priority": 0})
        elif action == delete_action:
            if QMessageBox.question(self, "Delete", f"Delete '{note.title}'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
                self.deleteNote.emit(note_id)
        elif action == rename_action:
            name, ok = QInputDialog.getText(self, "Rename", "New title:", text=note.title)
            if ok and name.strip(): self.renameNote.emit(note_id, name.strip())
        elif action == move_action: self.moveNoteToFolder.emit(note_id)
        elif action == preview_action: self.previewNote.emit(note_id)
        elif action == export_action: self.exportNote.emit(note_id)
        elif action == archive_action: self.updateNote.emit(note_id, {"is_archived": not getattr(note, 'is_archived', False)})

    def select_note_by_id(self, note_id):
        print(f"DEBUG: NoteList.select_note_by_id CALLED: note_id='{note_id}'")
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == note_id:
                print(f"DEBUG: Found item for note {note_id} at index {i}. Setting as current.")
                self.list_widget.setCurrentItem(item)
                # Manually trigger the selection logic so it emits noteSelected
                self.on_item_clicked(item)
                break

    def toggle_archived_view(self):
        self.showing_archived = not self.showing_archived
        self.back_btn.setVisible(self.showing_archived)
        self.new_note_btn.setVisible(not self.showing_archived)
        self.filter_notes(self.search_input.text())
