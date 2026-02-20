from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, QLabel, QPushButton, QLineEdit, QApplication, QColorDialog
)
from ui.zen_dialog import ZenInputDialog
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from ui.color_delegate import ColorDelegate, COLOR_ROLE
from util.icon_factory import get_premium_icon, get_combined_indicators
from ui.note_card_delegate import NoteCardDelegate
from ui.animations import pulse_button
from PyQt6.QtWidgets import QFileDialog
import ui.styles as styles
import os

VIEW_MODE_LIST = "list"
VIEW_MODE_GRID = "grid"

class NoteList(QWidget):
    noteSelected = pyqtSignal(str)
    createNoteRequest = pyqtSignal()
    deleteNote = pyqtSignal(str)
    restoreItem = pyqtSignal(str, str) # note_id, trash_path
    permanentDeleteItem = pyqtSignal(str) # trash_path
    emptyTrashRequest = pyqtSignal() # NEW
    clearNoteContentRequest = pyqtSignal(str)
    renameNote = pyqtSignal(str, str)
    updateNote = pyqtSignal(str, dict)  # Emit note_id, updates dict (e.g. {'is_pinned': True})
    insertNoteAtPosition = pyqtSignal(int)
    reorderNote = pyqtSignal(str, int)
    moveNoteToFolder = pyqtSignal(str)   # Emit note_id when user wants to move note
    exportNote = pyqtSignal(str)         # Emit note_id for export
    exportNoteWord = pyqtSignal(str)     # NEW
    previewNote = pyqtSignal(str)        # Emit note_id for preview
    viewModeChanged = pyqtSignal(str)    # Emit "list" or "grid"
    togglePanelRequest = pyqtSignal()   # Phase 46

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
        self.view_mode = VIEW_MODE_LIST
        
        self._setup_top_controls()
        self._setup_search()
        self._setup_list()
        
        # Apply initial constraints (Standardize across all startup paths)
        self.setMaximumWidth(400)
        self.setMinimumWidth(240)
        
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

        # HBox for controls
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(8)

        self.view_toggle_btn = QPushButton()
        self.view_toggle_btn.setObjectName("ViewToggleBtn")
        self.view_toggle_btn.setIconSize(QSize(20, 20))
        
        # Initial color based on theme_mode
        initial_color = "#FFFFFF" if self.theme_mode in ("dark", "dark_blue", "ocean_depth", "noir_ember") else "#09090b"
        self.view_toggle_btn.setIcon(get_premium_icon("layout_grid", color=initial_color)) 
        
        self.view_toggle_btn.setToolTip("Switch to Grid View")
        self.view_toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.view_toggle_btn.setFixedSize(32, 32)
        self.view_toggle_btn.clicked.connect(lambda: (pulse_button(self.view_toggle_btn), self.toggle_view_mode()))
        
        self.panel_toggle_btn = QPushButton()
        self.panel_toggle_btn.setObjectName("ViewToggleBtn") # Re-use same premium style
        self.panel_toggle_btn.setIconSize(QSize(20, 20))
        self.panel_toggle_btn.setIcon(get_premium_icon("panel_toggle", color=initial_color))
        self.panel_toggle_btn.setToolTip("Hide Note Panel")
        self.panel_toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.panel_toggle_btn.setFixedSize(32, 32)
        self.panel_toggle_btn.clicked.connect(lambda: (pulse_button(self.panel_toggle_btn), self.togglePanelRequest.emit()))
        
        controls_layout.addWidget(self.panel_toggle_btn)
        controls_layout.addWidget(self.view_toggle_btn)

        self.new_note_btn = QPushButton(" New Note")
        self.new_note_btn.setIcon(get_premium_icon("plus", color="white"))
        self.new_note_btn.setObjectName("NewNoteBtn")
        self.new_note_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.new_note_btn.clicked.connect(lambda: (pulse_button(self.new_note_btn), self.createNoteRequest.emit()))
        
        controls_layout.addWidget(self.new_note_btn)
        top_layout.addLayout(controls_layout)
        
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
        
        # Delegates
        self.list_delegate = ColorDelegate(self.list_widget)
        self.grid_delegate = NoteCardDelegate(self.list_widget)
        
        self.list_widget.setItemDelegate(self.list_delegate)
        
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
        
    def load_notes(self, notes, folder_id=None):
        self.current_notes = notes
        self.current_folder_id = folder_id
        
        # UI Updates based on context
        is_trash = folder_id == "TRASH_ROOT"
        self.new_note_btn.setVisible(not is_trash)
        
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
                # Use theme-aware foreground color
                c = styles.ZEN_THEME.get(self.theme_mode, styles.ZEN_THEME["light"])
                icon_color = c.get('sidebar_fg', c.get('foreground', '#000000'))
                
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
                indicators = ["note"]
                if getattr(note, 'is_pinned', False): indicators.append("pin")
                if getattr(note, 'is_locked', False): indicators.append("lock")
                
                item = QListWidgetItem(f"{idx}. {prefix}{note_title.strip()}")
                c = styles.ZEN_THEME.get(self.theme_mode, styles.ZEN_THEME["light"])
                icon_color = c.get('sidebar_fg', c.get('foreground', '#000000'))
                item.setIcon(get_combined_indicators(indicators, color=icon_color))
                item.setIcon(get_combined_indicators(indicators, color=icon_color))
                item.setData(Qt.ItemDataRole.UserRole, note.id)
                # Pass Note Object for Delegate
                item.setData(Qt.ItemDataRole.UserRole + 1, note)
                
                if getattr(note, 'color', None):
                    item.setData(COLOR_ROLE, note.color)
                self.list_widget.addItem(item)
            except Exception: continue
        
    def on_item_clicked(self, item):
        if not item: return
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
        c = styles.ZEN_THEME.get(mode, styles.ZEN_THEME["light"])
        icon_color = c.get('sidebar_fg', c.get('foreground', '#000000'))
        
        self.back_btn.setIcon(get_premium_icon("back", color=icon_color))
        
        # Refresh View Toggle Icon (Phase 45)
        icon_name = "layout_list" if self.view_mode == VIEW_MODE_GRID else "layout_grid"
        self.view_toggle_btn.setIcon(get_premium_icon(icon_name, color=icon_color))
        self.panel_toggle_btn.setIcon(get_premium_icon("panel_toggle", color=icon_color))
        
        self.grid_delegate.set_theme_mode(mode)
        self.list_delegate.set_theme_mode(mode) # Ensure List Delegate gets theme too
        self.filter_notes(self.search_input.text())
        
    def toggle_view_mode(self):
        new_mode = VIEW_MODE_GRID if self.view_mode == VIEW_MODE_LIST else VIEW_MODE_LIST
        self.set_view_mode(new_mode)

    def set_view_mode(self, mode):
        if self.view_mode == mode: return
        self.view_mode = mode
        
        self.list_widget.setItemDelegate(self.list_delegate)
        self.list_widget.setSpacing(2) # Reduced base gap between note cards
        
        # Use theme-aware color for icons
        c = styles.ZEN_THEME.get(self.theme_mode, styles.ZEN_THEME["light"])
        icon_color = c.get('sidebar_fg', c.get('foreground', '#000000'))
        
        if mode == VIEW_MODE_GRID:
            self.list_widget.setViewMode(QListWidget.ViewMode.IconMode)
            self.list_widget.setItemDelegate(self.grid_delegate)
            self.list_widget.setSpacing(10)
            # Enable Snap for better grid reordering
            self.list_widget.setMovement(QListWidget.Movement.Snap)
            self.list_widget.setResizeMode(QListWidget.ResizeMode.Adjust)
            self.view_toggle_btn.setIcon(get_premium_icon("layout_list", color=icon_color))
            self.view_toggle_btn.setToolTip("Switch to List View")
            
            # Limit stretching in Grid mode to keep cards tight and organized
            self.setMaximumWidth(450) 
        else:
            self.list_widget.setViewMode(QListWidget.ViewMode.ListMode)
            self.list_widget.setItemDelegate(self.list_delegate)
            self.list_widget.setSpacing(2) # Reduced padding gap in list mode
            # Standard list movement
            self.list_widget.setMovement(QListWidget.Movement.Free)
            self.list_widget.setResizeMode(QListWidget.ResizeMode.Adjust)
            self.view_toggle_btn.setIcon(get_premium_icon("layout_grid", color=icon_color))
            self.view_toggle_btn.setToolTip("Switch to Grid View")
            
            # Stricter width limit for List mode to match card cap (400px)
            self.setMaximumWidth(400)
        
        self.list_widget.setResizeMode(QListWidget.ResizeMode.Adjust)
        
        # Refresh to apply resizing
        self.list_widget.doItemsLayout()
        self.viewModeChanged.emit(mode)
        
    def show_context_menu(self, pos):
        item = self.list_widget.itemAt(pos)
        if not item: return
        from PyQt6.QtWidgets import QMenu, QMessageBox
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
        bg_color_action = menu.addAction(get_premium_icon("layout"), "Set Page Background...") # NEW
        page_size_action = menu.addAction(get_premium_icon("file_text"), "Set Page Size...") # NEW
        lock_text = "Unlock Note" if getattr(note, 'is_locked', False) else "Lock Note"
        lock_action = menu.addAction(lock_text)

        menu.addSeparator()
        # Trash Specific Actions
        is_trash = hasattr(self, 'current_folder_id') and self.current_folder_id == "TRASH_ROOT"
        
        if is_trash:
            restore_action = menu.addAction(get_premium_icon("rotate_ccw", color="#10B981"), "Restore Item") # Emerald Green
            menu.addSeparator()
            perm_delete_action = menu.addAction(get_premium_icon("delete", color="#EF4444"), "Delete Permanently") # Red
            
            # Disable standard actions in trash
            rename_action = None
            clear_action = None
            delete_action = None
            move_action = None
            archive_action = None
            preview_action = None
            export_action = None
            export_word_action = None
        else:
            restore_action = None
            perm_delete_action = None
            rename_action = menu.addAction("Rename Note")
            if getattr(note, 'is_locked', False):
                rename_action.setEnabled(False)
                clear_action = menu.addAction("Clear All Content (Locked)"); clear_action.setEnabled(False)
                delete_action = menu.addAction("Move to Trash (Locked)"); delete_action.setEnabled(False)
            else:
                clear_action = menu.addAction("🗑 Clear All Content")
                delete_action = menu.addAction("Move to Trash")
            
            move_action = menu.addAction("Move to Notebook")
            
            menu.addSeparator()
            
            # Cover Image Management (Phase 43)
            current_cover = getattr(note, 'cover_image', None)
            has_cover = current_cover and os.path.exists(current_cover)
            
            if has_cover:
                set_cover_action = menu.addAction("Change Cover Image...")
                remove_cover_action = menu.addAction("Remove Cover Image")
            else:
                set_cover_action = menu.addAction("Set Cover Image...")
                remove_cover_action = None
                
            edit_desc_action = menu.addAction("Edit Description...")
            
            menu.addSeparator()
            preview_action = menu.addAction("Preview Note PDF")
            export_action = menu.addAction("Export to PDF")
            export_word_action = menu.addAction("Export to Word (.docx)") # NEW
            
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
        elif action == bg_color_action:
            from PyQt6.QtGui import QColor
            initial_color = getattr(note, 'background_color', '#FFFFFF') or '#FFFFFF'
            initial = QColor(initial_color)
            color = QColorDialog.getColor(initial, self, "Select Page Background")
            if color.isValid(): self.updateNote.emit(note_id, {"background_color": color.name()})
        elif action == page_size_action:
            from ui.zen_dialog import PageSizeDialog
            current_size = getattr(note, 'page_size', 'free')
            new_size, ok = PageSizeDialog.getPageSize(self, current_size, self.theme_mode)
            if ok: self.updateNote.emit(note_id, {"page_size": new_size})
        elif action == lock_action: self.updateNote.emit(note_id, {"is_locked": not getattr(note, 'is_locked', False)})
        elif action == p1: self.updateNote.emit(note_id, {"priority": 1})
        elif action == p2: self.updateNote.emit(note_id, {"priority": 2})
        elif action == p3: self.updateNote.emit(note_id, {"priority": 3})
        elif action == pn: self.updateNote.emit(note_id, {"priority": 0})
        elif restore_action and action == restore_action:
            trash_path = getattr(note, '_trash_path', None)
            if trash_path:
                self.restoreItem.emit(note_id, trash_path)
        elif perm_delete_action and action == perm_delete_action:
            trash_path = getattr(note, '_trash_path', None)
            if trash_path:
                if QMessageBox.question(self, "Delete Permanently", f"Are you sure you want to permanently delete this item?\nThis action cannot be undone.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
                    self.permanentDeleteItem.emit(trash_path)
        elif delete_action and action == delete_action:
            self.deleteNote.emit(note_id)
        elif action == clear_action:
            if QMessageBox.question(self, "Clear Content", f"Are you sure you want to clear all content in '{note.title}'?\nThis action cannot be undone.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
                self.clearNoteContentRequest.emit(note_id)
        elif action == rename_action:
            name, ok = ZenInputDialog.getText(self, "Rename", "New title:", text=note.title)
            if ok and name.strip(): self.renameNote.emit(note_id, name.strip())
        elif action == move_action: self.moveNoteToFolder.emit(note_id)
        elif action == set_cover_action:
            file_path, _ = QFileDialog.getOpenFileName(self, "Select Cover Image", "", "Images (*.png *.jpg *.jpeg *.webp)")
            if file_path:
                self.updateNote.emit(note_id, {"cover_image": file_path})
        elif remove_cover_action and action == remove_cover_action:
             if QMessageBox.question(self, "Remove Cover", "Remove cover image?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
                 self.updateNote.emit(note_id, {"cover_image": None})
        elif action == edit_desc_action:
            desc, ok = ZenInputDialog.getText(self, "Edit Description", "Description:", text=getattr(note, 'description', "") or "")
            if ok:
                self.updateNote.emit(note_id, {"description": desc})
        elif action == preview_action: self.previewNote.emit(note_id)
        elif action == export_action: self.exportNote.emit(note_id)
        elif action == export_word_action: self.exportNoteWord.emit(note_id) # NEW
        elif archive_action and action == archive_action: self.updateNote.emit(note_id, {"is_archived": not getattr(note, 'is_archived', False)})

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

    def resizeEvent(self, event):
        """Phase 40: Trigger layout update on resize for responsive cards."""
        super().resizeEvent(event)
        if hasattr(self, 'list_widget') and self.view_mode == VIEW_MODE_GRID:
            self.list_widget.scheduleDelayedItemsLayout()
