from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QWidget, QLabel, QPushButton, QMessageBox, 
    QSplitter, QFileDialog, QToolBar, QApplication,
    QMainWindow, QStatusBar, QMenu, QLineEdit, QListWidget, QListWidgetItem, QProgressBar, QPushButton,
    QProgressDialog, QDialog, QFormLayout, QComboBox, QCheckBox, QSlider, QGroupBox, QSpinBox, QTextEdit, QTabWidget,
    QAbstractItemView, QStyleFactory, QListWidgetItem, QToolButton, QStyle, QButtonGroup, QRadioButton, QTextBrowser, QFrame,
    QStackedWidget
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QProcess, QPoint, QRectF, QPointF, QRect
from PyQt6.QtGui import QAction, QIcon, QKeySequence, QShortcut, QPainter, QPen, QColor, QPixmap, QImage, QMouseEvent, QPaintEvent, QTextCursor
from util.icon_factory import get_premium_icon

from ui.sidebar import Sidebar
from ui.note_list import NoteList
from ui.editor import TextEditor
from ui.widgets import EmptyStateWidget
from ui.whiteboard_widget import WhiteboardWidget
from storage.data_manager import DataManager
from models.note import Note
from models.folder import Folder
from util.shortcut_manager import ShortcutManager
from ui.shortcut_dialog import ShortcutDialog
from ui.move_note_dialog import MoveNoteDialog
from util.logger import logger
import ui.styles as styles
# PDF Export to be imported later
import json
import os
import sys
from datetime import datetime
from word_export import export_note_to_docx, export_folder_to_docx # NEW
from ui.note_overlay import NoteOverlayDialog
from ui.title_bar import CustomTitleBar
from ui.zen_dialog import ZenInputDialog, ZenItemDialog
from ui.animations import animate_splitter, crossfade_theme, fade_widget

class MetadataBar(QFrame):
    """Subtle bar displaying note metadata with technical typography."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(28)
        self.setObjectName("MetadataBar")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 0, 15, 0)
        layout.setSpacing(20)
        
        # IBM Plex Mono for that 'technical precision' feel
        mono_style = 'font-family: "IBM Plex Mono", monospace; font-size: 11px; opacity: 0.7;'
        
        self.lbl_words = QLabel("0 WORDS")
        self.lbl_words.setStyleSheet(mono_style)
        
        self.lbl_chars = QLabel("0 CHARS")
        self.lbl_chars.setStyleSheet(mono_style)
        
        self.lbl_modified = QLabel("LAST MODIFIED: --")
        self.lbl_modified.setStyleSheet(mono_style)
        
        layout.addWidget(self.lbl_words)
        layout.addWidget(self.lbl_chars)
        layout.addStretch()
        layout.addWidget(self.lbl_modified)
        
    def update_stats(self, text, last_modified=None):
        words = len(text.split())
        chars = len(text)
        self.lbl_words.setText(f"{words} WORDS")
        self.lbl_chars.setText(f"{chars} CHARS")
        if last_modified:
            self.lbl_modified.setText(f"LAST MODIFIED: {last_modified.upper()}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Zen Notes")
        
        # Frameless Window Setup
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Default Size & Positioning
        self.resize(1200, 800)
        
        # Center on screen
        qr = self.frameGeometry()
        cp = QApplication.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
        
        # Then Maximize
        self.setWindowState(Qt.WindowState.WindowMaximized)
        self.data_manager = DataManager()
        self.shortcut_manager = ShortcutManager(self.data_manager)
        self.current_folder = None
        self.current_note = None
        self.is_note_locked = False
        self._navigating_via_link = False
        
        # Setup UI components (Sidebar/NoteList first, then Splitter and Editor)
        self.setup_ui()
        self.setup_menu()
        
        if hasattr(self.editor, 'requestShortcutDialog'):
             self.editor.requestShortcutDialog.connect(self.show_shortcut_dialog)
             
        # Sidebar Toggle Shortcut (Phase 46 Refinement)
        from PyQt6.QtGui import QShortcut, QKeySequence
        self.toggle_shortcut = QShortcut(QKeySequence("Ctrl+B"), self)
        self.toggle_shortcut.activated.connect(self.toggle_note_panel)
        
        # Startup Animation
        self.setWindowOpacity(0.0)
        from PyQt6.QtCore import QPropertyAnimation, QEasingCurve
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(600)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.start()
        
        # Initial Load
        # Initial Load
        self.refresh_folders()
        
        # State tracking for image editing
        self.editing_image_id = None
        self.highlight_numbering_continuous = False # Default: Restart per note

        # Window Resizing State
        self._resize_margin = 8
        self._is_resizing = False
        self._resize_edges = Qt.Edge(0)
        self.setMouseTracking(True) # Required for edge detection without clicking

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            edges = self._get_edges(event.pos())
            if edges:
                self._is_resizing = True
                self._resize_edges = edges
                self._drag_pos = event.globalPosition().toPoint()
                self._start_geometry = self.geometry()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        edges = self._get_edges(event.pos())
        if not self._is_resizing:
            if edges == (Qt.Edge.BottomEdge | Qt.Edge.RightEdge): self.setCursor(Qt.CursorShape.SizeBDiagCursor)
            elif edges == (Qt.Edge.TopEdge | Qt.Edge.LeftEdge): self.setCursor(Qt.CursorShape.SizeBDiagCursor)
            elif edges == (Qt.Edge.TopEdge | Qt.Edge.RightEdge): self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            elif edges == (Qt.Edge.BottomEdge | Qt.Edge.LeftEdge): self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            elif edges & (Qt.Edge.LeftEdge | Qt.Edge.RightEdge): self.setCursor(Qt.CursorShape.SizeHorCursor)
            elif edges & (Qt.Edge.TopEdge | Qt.Edge.BottomEdge): self.setCursor(Qt.CursorShape.SizeVerCursor)
            else: self.setCursor(Qt.CursorShape.ArrowCursor)
        else:
            new_pos = event.globalPosition().toPoint()
            diff = new_pos - self._drag_pos
            new_geom = QRect(self._start_geometry)
            
            if self._resize_edges & Qt.Edge.LeftEdge:
                new_geom.setLeft(self._start_geometry.left() + diff.x())
            if self._resize_edges & Qt.Edge.RightEdge:
                new_geom.setRight(self._start_geometry.right() + diff.x())
            if self._resize_edges & Qt.Edge.TopEdge:
                new_geom.setTop(self._start_geometry.top() + diff.y())
            if self._resize_edges & Qt.Edge.BottomEdge:
                new_geom.setBottom(self._start_geometry.bottom() + diff.y())
            
            # Constraints
            if new_geom.width() >= self.minimumWidth() and new_geom.height() >= self.minimumHeight():
                self.setGeometry(new_geom)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._is_resizing = False
        self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseReleaseEvent(event)

    def _get_edges(self, pos):
        edges = Qt.Edge(0)
        if pos.x() <= self._resize_margin: edges |= Qt.Edge.LeftEdge
        if pos.x() >= self.width() - self._resize_margin: edges |= Qt.Edge.RightEdge
        if pos.y() <= self._resize_margin: edges |= Qt.Edge.TopEdge
        if pos.y() >= self.height() - self._resize_margin: edges |= Qt.Edge.BottomEdge
        return edges

    def setup_ui(self):
        # 0. Initialize Title Bar Early
        self.title_bar = CustomTitleBar(self)
        
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setObjectName("MainContainer")

        # 1. Sidebar
        self.sidebar = Sidebar()
        self.sidebar.createFolder.connect(self.create_folder)
        self.sidebar.deleteFolder.connect(self.delete_folder)
        self.sidebar.folderSelected.connect(self.select_folder)
        self.sidebar.exportFolder.connect(self.export_folder_by_id)
        self.sidebar.exportFolderWord.connect(self.export_folder_word) # NEW
        self.sidebar.exportWhiteboard.connect(self.export_folder_whiteboard)
        self.sidebar.updateFolder.connect(self.update_folder)
        self.sidebar.renameFolder.connect(self.rename_folder)
        self.sidebar.reorderFolder.connect(self.reorder_folder)
        self.sidebar.createNotebook.connect(self.create_notebook)
        self.sidebar.deleteNotebook.connect(self.delete_notebook)
        self.sidebar.toggleTheme.connect(self.toggle_theme)
        self.sidebar.wrapToggled.connect(self.toggle_wrap)
        self.sidebar.requestHighlightPreview.connect(self.show_highlight_preview)
        self.sidebar.requestPdfPreview.connect(self.show_pdf_preview)
        self.sidebar.lockToggled.connect(self.toggle_note_lock)
        self.sidebar.panelToggleRequest.connect(self.toggle_note_panel)
        self.main_splitter.addWidget(self.sidebar)

        # 2. Note List
        self.note_list = NoteList()
        self.note_list.setMinimumWidth(0)
        self.note_list.noteSelected.connect(self.select_note)
        self.note_list.createNoteRequest.connect(self.create_note)
        self.note_list.deleteNote.connect(self.delete_note)
        self.note_list.renameNote.connect(self.rename_note)
        self.note_list.reorderNote.connect(self.reorder_note)
        self.note_list.insertNoteAtPosition.connect(self.insert_note_at_position)
        self.note_list.updateNote.connect(self.update_note) # NEW
        self.note_list.togglePanelRequest.connect(self.toggle_note_panel)
        self.note_list.moveNoteToFolder.connect(self.move_note_to_folder_with_dialog)
        self.note_list.exportNote.connect(self.export_note_by_id) 
        self.note_list.exportNoteWord.connect(self.export_note_by_id_word) # NEW
        self.note_list.previewNote.connect(self.preview_note_by_id)
        self.note_list.clearNoteContentRequest.connect(self.clear_note_content) # NEW
        self.note_list.viewModeChanged.connect(self.on_view_mode_changed) # NEW: Persist View Mode
        self.note_list.restoreItem.connect(self.restore_item) # NEW: Trash Restore
        self.note_list.permanentDeleteItem.connect(self.permanent_delete_trash_item) # NEW: Permanent Delete
        self.note_list.emptyTrashRequest.connect(self.empty_trash) # NEW: Empty Trash
        self.main_splitter.addWidget(self.note_list)

        # 3. Editor Content Splitter (Nested)
        # Holds [HighlightView, WhiteboardPlaceholder, Editor]
        self.content_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Right Side Container (Editor + Metadata + TitleBar)
        self.editor_container = QWidget()
        editor_layout = QVBoxLayout(self.editor_container)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.setSpacing(0)
        
        # Highlight Preview View (Hidden by default, on the LEFT like whiteboard)
        self.highlight_view = QTextBrowser()
        self.highlight_view.setReadOnly(True) # Fix: ReadOnly for button behavior
        self.highlight_view.setVisible(False)
        self.highlight_view.setOpenLinks(False)
        self.highlight_view.anchorClicked.connect(self.handle_highlight_link)
        self.content_splitter.addWidget(self.highlight_view)

        # Whiteboard Widget (Hidden by default, embedded like highlight preview)
        self.whiteboard_widget = WhiteboardWidget()
        self.whiteboard_widget.setVisible(False)
        self.whiteboard_widget.contentChanged.connect(lambda: self.wb_autosave_timer.start())        # Connect Whiteboard Signals
        self.whiteboard_widget.closed.connect(self.on_whiteboard_closed)
        self.whiteboard_widget.insert_requested.connect(self.insert_image_to_note)
        self.content_splitter.addWidget(self.whiteboard_widget)

        # 4. Editor
        self.editor = TextEditor(data_manager=self.data_manager, shortcut_manager=self.shortcut_manager)
        current_theme = self.data_manager.get_setting("theme_mode", "light")
        self.editor.set_theme_mode(current_theme)
        
        # Disable editor initially (until a note is selected)
        self.editor.editor.setReadOnly(True)
        
        self.editor.contentChanged.connect(self.auto_save_note)
        self.editor.exportNoteRequest.connect(self.export_current_note_pdf)
        self.editor.exportWordRequest.connect(self.export_current_note_word) # NEW
        self.editor.edit_whiteboard_requested.connect(self.jump_to_whiteboard)
        self.editor.request_open_note.connect(self.open_note_by_id)
        self.editor.request_open_note_overlay.connect(self.open_note_overlay)
        
        # 5. Metadata Bar
        self.metadata_bar = MetadataBar()
        
        editor_layout.addWidget(self.editor)
        editor_layout.addWidget(self.metadata_bar)
        
        # 6. Stacked Widget for Empty State vs Editor
        self.empty_state = EmptyStateWidget()
        self.editor_stack = QStackedWidget()
        self.editor_stack.addWidget(self.empty_state)
        self.editor_stack.addWidget(self.editor_container)
        
        # 7. Persistent Wrapper for Title Bar + Editor Stack
        # This ensures window controls (Min/Max/Close) stay visible in empty state.
        self.right_panel_container = QWidget()
        right_panel_layout = QVBoxLayout(self.right_panel_container)
        right_panel_layout.setContentsMargins(0, 0, 0, 0)
        right_panel_layout.setSpacing(0)
        
        right_panel_layout.addWidget(self.title_bar)
        right_panel_layout.addWidget(self.editor_stack)
        
        self.content_splitter.addWidget(self.right_panel_container)
        
        # Connect editor text changes to metadata updates
        self.editor.editor.textChanged.connect(self.refresh_metadata)
        
        # Connect Editor Toolbar to Custom Title Bar
        self.title_bar.set_editor_toolbar_actions(self.editor.get_toolbar_actions())
        
        # Add nested splitter to main splitter
        self.main_splitter.addWidget(self.content_splitter)

        # Set stretch factors for MAIN splitter
        self.main_splitter.setSizes([200, 300, 700])
        # Ensure all panels are non-collapsible to prevent disappearance
        self.main_splitter.setCollapsible(0, False) # Folders
        self.main_splitter.setCollapsible(1, False) # Notes
        self.main_splitter.setCollapsible(2, False) # Editor
        
        # Enforce width constraints for sidebars
        self.sidebar.setMinimumWidth(200)
        self.sidebar.setMaximumWidth(350) # Prevent Folders from becoming "too big"
        self.note_list.setMinimumWidth(240)
        self.note_list.setMaximumWidth(400) # Hard limit for Notes List to prevent "fat" cards
        
        # Set stretch factors: Sidebar and NoteList stay fixed, Editor takes extra space
        self.main_splitter.setStretchFactor(0, 0)
        self.main_splitter.setStretchFactor(1, 0)
        self.main_splitter.setStretchFactor(2, 1)

        # Connect splitter signal to resize images when sidebar is resized
        self.main_splitter.splitterMoved.connect(self._handle_splitter_resize)
        
        # 4. Final Setup: Content only (Title Bar is nested)
        self.main_container = QWidget()
        self.main_container.setObjectName("MainWindowContainer")
        self.main_layout = QVBoxLayout(self.main_container)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        self.main_layout.addWidget(self.main_splitter)
        
        self.setCentralWidget(self.main_container)
        
        # Autosave Timer for Whiteboard (Debouncing)
        self.wb_autosave_timer = QTimer()
        self.wb_autosave_timer.setSingleShot(True)
        self.wb_autosave_timer.setInterval(2000) # Wait 2 seconds after last stroke
        self.wb_autosave_timer.timeout.connect(self.auto_save_whiteboard)
        
        # Status Bar for feedback
        self.statusBar().showMessage("Ready", 2000)
        
        # Save Debounce Timer
        self.save_timer = QTimer()
        self.save_timer.setSingleShot(True)
        self.save_timer.setInterval(500) # Wait 500ms after last keystroke
        self.save_timer.timeout.connect(self._perform_save)
        
        # Apply Saved Theme
        current_theme = self.data_manager.get_setting("theme_mode", "light")
        self.apply_theme(current_theme)
        
        # Apply Saved Wrap Mode
        wrap_enabled = self.data_manager.get_setting("wrap_mode", False)
        self.sidebar.set_wrap_mode(wrap_enabled)
        self.note_list.set_wrap_mode(wrap_enabled)

        # Restore Last Selected Folder
        last_folder_id = self.data_manager.get_setting("last_selected_folder_id")
        if last_folder_id:
            # Check if folder still exists
            if self.data_manager.get_folder_by_id(last_folder_id):
                self.sidebar.select_folder_by_id(last_folder_id)
                self.select_folder(last_folder_id)

    def setup_menu(self):
        # We removed the visual Menu Bar but kept the shortcuts by adding actions to self
        
        # Store refs for Dynamic Updates
        self.action_new_note = QAction("New Note", self)
        self.action_new_note.setShortcut(self.shortcut_manager.get_shortcut("global_new_note"))
        self.action_new_note.triggered.connect(self.create_note)
        self.addAction(self.action_new_note)

        self.action_new_folder = QAction("New Folder", self)
        self.action_new_folder.setShortcut(self.shortcut_manager.get_shortcut("global_new_folder"))
        self.action_new_folder.triggered.connect(self.sidebar.prompt_new_folder)
        self.addAction(self.action_new_folder)

        self.action_save = QAction("Save", self)
        self.action_save.setShortcut(self.shortcut_manager.get_shortcut("global_save"))
        self.action_save.triggered.connect(self.save_current_note)
        self.addAction(self.action_save)

        # New Shortcuts
        self.action_theme = QAction("Toggle Theme", self)
        self.action_theme.setShortcut(self.shortcut_manager.get_shortcut("global_toggle_theme"))
        self.action_theme.triggered.connect(lambda _checked: self.toggle_theme())
        self.addAction(self.action_theme)

        self.action_highlight_prev = QAction("Highlight Preview", self)
        self.action_highlight_prev.setShortcut(self.shortcut_manager.get_shortcut("global_highlight_preview"))
        self.action_highlight_prev.triggered.connect(self.show_highlight_preview)
        self.addAction(self.action_highlight_prev)

        self.action_pdf_prev = QAction("PDF Preview", self)
        self.action_pdf_prev.setShortcut(self.shortcut_manager.get_shortcut("global_pdf_preview"))
        self.action_pdf_prev.triggered.connect(self.show_pdf_preview)
        self.addAction(self.action_pdf_prev)
        
        # Explicitly hide the menu bar just in case
        self.menuBar().setVisible(False)

    # --- Logic ---
    
    def toggle_theme(self, mode=None):
        # Guard: QAction.triggered(bool) can pass False as mode — treat non-string as None
        if not isinstance(mode, str):
            mode = None
            
        if mode is None:
            # Fallback: cycle if called without argument
            current = self.data_manager.get_setting("theme_mode", "light")
            # Ensure current is actually a string (hard reset if settings were corrupted)
            if not isinstance(current, str):
                current = "light"
                
            modes = ["light", "dark", "dark_blue", "rose", "ocean_depth", "forest_sage", "noir_ember"]
            try:
                idx = modes.index(current)
                mode = modes[(idx + 1) % len(modes)]
            except (ValueError, IndexError):
                mode = "light"
        
        self.data_manager.set_setting("theme_mode", mode)
        print(f"DEBUG: toggle_theme called with mode='{mode}'")
        
        # Animate theme switch
        crossfade_theme(self, lambda: self.apply_theme(mode))
        
        # FIX: Refresh highlight preview to apply new theme CSS
        self.refresh_highlight_preview_if_visible()
        
    def apply_theme(self, mode):
        # Apply global stylesheet
        css = styles.get_stylesheet(mode)
        
        # Map custom themes to qdarktheme base
        dark_themes = {"dark", "dark_blue", "ocean_depth", "noir_ember"}
        light_themes = {"light", "rose", "forest_sage"}
        
        if mode in dark_themes:
            base_mode = "dark"
        elif mode in light_themes:
            base_mode = "light"
        else:
            # Custom theme — detect from background color
            c = styles.ZEN_THEME.get(mode, styles.ZEN_THEME["light"])
            bg = c.get("background", "#FFFFFF")
            # Simple brightness check
            if bg.startswith("#"):
                r = int(bg[1:3], 16)
                base_mode = "dark" if r < 128 else "light"
            else:
                base_mode = "light"
        
        try:
            import qdarktheme
            # Support for older versions (0.1.7) which only have load_stylesheet
            if hasattr(qdarktheme, 'setup_theme'):
                 qdarktheme.setup_theme(base_mode)
                 QApplication.instance().setStyleSheet(qdarktheme.load_stylesheet(base_mode) + css)
            elif hasattr(qdarktheme, 'load_stylesheet'):
                 # v0.1.7 style
                 qt_css = qdarktheme.load_stylesheet(base_mode)
                 QApplication.instance().setStyleSheet(qt_css + css)
            else:
                 # Fallback
                 QApplication.instance().setStyleSheet(css)
        except Exception as e:
            logger.error(f"Theme setup error: {e}")
            QApplication.instance().setStyleSheet(css)

        # Propagate theme to sidebar and note list
        print(f"DEBUG: apply_theme propagating mode='{mode}' to components")
        if hasattr(self, 'sidebar'):
            self.sidebar.set_theme_mode(mode)
        if hasattr(self, 'note_list'):
            self.note_list.set_theme_mode(mode)
        
        # Propagate theme to editor for highlighting logic
        if hasattr(self, 'editor'):
            self.editor.set_theme_mode(mode)

        if hasattr(self, 'whiteboard_widget'):
            self.whiteboard_widget.set_theme_mode(mode)

        if hasattr(self, 'empty_state'):
            self.empty_state.set_theme_mode(mode)
        
        if hasattr(self, 'title_bar'):
            self.title_bar.set_theme_mode(mode)
        
        # Trigger initial refresh
        if hasattr(self, 'editor'):
            self.editor._refresh_toolbar_icons(mode)
            
        # Update open overlays
        if hasattr(self, '_overlays'):
            for overlay in self._overlays:
                try:
                    overlay.apply_theme(mode)
                except Exception as e:
                    logger.error(f"Error updating overlay theme: {e}")

    def toggle_wrap(self, enabled):
        """Handle wrap mode toggle from sidebar."""
        # Apply wrap mode to both lists
        self.sidebar.set_wrap_mode(enabled)
        self.note_list.set_wrap_mode(enabled)
        # Save preference
        self.data_manager.set_setting("wrap_mode", enabled)

    def refresh_folders(self):
        self.sidebar.load_notebooks(self.data_manager.notebooks)
        self.sidebar.all_folders = self.data_manager.folders
        self.sidebar.refresh_list()

    def create_folder(self, name, notebook_id=None):
        if self.check_lock(): return
        folder = self.data_manager.add_folder(name)
        # Associate with notebook
        self.data_manager.add_folder_to_notebook(folder.id, notebook_id)
        self.refresh_folders()
        self.sidebar.select_folder_by_id(folder.id)
        self.select_folder(folder.id)

    def create_notebook(self, name):
        if self.check_lock(): return
        self.data_manager.add_notebook(name)
        self.sidebar.update_notebook_selector()

    def delete_notebook(self, nb_id):
        self.data_manager.delete_notebook(nb_id)
        self.refresh_folders()
        
    def update_folder(self, folder_id, updates):
        """Update folder attributes (pin, priority) and save."""
        folder = self.data_manager.get_folder_by_id(folder_id)
        if folder:
            # Apply updates
            if "is_pinned" in updates:
                folder.is_pinned = updates["is_pinned"]
            if "priority" in updates:
                folder.priority = updates["priority"]
            if "is_archived" in updates:
                folder.is_archived = updates["is_archived"]
            if "color" in updates:
                folder.color = updates["color"]
            if "is_locked" in updates:
                folder.is_locked = updates["is_locked"]
            if "cover_image" in updates:
                folder.cover_image = updates["cover_image"]
            if "description" in updates:
                folder.description = updates["description"]
            if "view_mode" in updates:
                folder.view_mode = updates["view_mode"]
            
            # Save Metadata to Settings
            folders_meta = self.data_manager.get_setting("folders_meta", {})
            
            # We need to ensure we have an entry for this folder
            if folder_id not in folders_meta:
                folders_meta[folder_id] = {}
            
            # Update the specific fields
            folders_meta[folder_id]["is_pinned"] = folder.is_pinned
            folders_meta[folder_id]["priority"] = folder.priority
            folders_meta[folder_id]["is_archived"] = folder.is_archived
            folders_meta[folder_id]["color"] = folder.color
            folders_meta[folder_id]["is_locked"] = folder.is_locked
            folders_meta[folder_id]["cover_image"] = folder.cover_image
            folders_meta[folder_id]["description"] = folder.description
            folders_meta[folder_id]["view_mode"] = folder.view_mode
            
            self.data_manager.set_setting("folders_meta", folders_meta)
            self.refresh_folders()
            return

        if folder_id == "ROOT":
            if "notebook_rename" in updates:
                nb_id, new_name = updates["notebook_rename"]
                nb = next((n for n in self.data_manager.notebooks if n.id == nb_id), None)
                if nb:
                    nb.name = new_name
                    self.data_manager.save_settings()
            return
            
        folder = self.data_manager.get_folder_by_id(folder_id)

    def reorder_folder(self, folder_id, new_index):
        """Handle folder reordering from Sidebar."""
        # Note: Since switching to QTreeWidget, simple indexing is different.
        # This is a placeholder or partial implementation for now to prevent crash.
        pass

    def update_note(self, note_id, updates):
        """Update note attributes (pin, priority) and save."""
        if not self.current_folder: return
        
        note = self.current_folder.get_note_by_id(note_id)
        if note:
            # Apply updates
            if "is_pinned" in updates:
                note.is_pinned = updates["is_pinned"]
            if "priority" in updates:
                note.priority = updates["priority"]
            if "is_archived" in updates:
                note.is_archived = updates["is_archived"]
            if "color" in updates:
                note.color = updates["color"]
            if "is_locked" in updates:
                note.is_locked = updates["is_locked"]
            if "cover_image" in updates:
                note.cover_image = updates["cover_image"]
            if "description" in updates:
                note.description = updates["description"]
            if "closed_at" in updates:
                note.closed_at = updates["closed_at"]
                
            # Save via Data Manager (using save_note to ensure persistence in FS mode)
            self.data_manager.save_note(self.current_folder, note)
            
            # Refresh List (preserves selection if possible)
            # Re-sort happens automatically in load_notes -> filter_notes
            self.note_list.load_notes(self.current_folder.notes)
            
            # Restore selection
            self.note_list.select_note_by_id(note_id)

    def toggle_note_panel(self):
        """Toggles the visibility of the note list panel using a 'drawer' style (Phase 46.2)."""
        sizes = self.main_splitter.sizes()
        sidebar_w, list_w, editor_w = sizes
        
        if list_w > 0:
            # Collapse
            self._last_note_list_width = list_w
            target_sizes = [sidebar_w, 0, editor_w + list_w]
        else:
            # Expand
            target_w = getattr(self, '_last_note_list_width', 300)
            # Ensure we don't reduce editor to nothing
            new_editor_w = max(100, editor_w - target_w)
            target_sizes = [sidebar_w, target_w, new_editor_w]
            
        animate_splitter(self.main_splitter, target_sizes)


    def delete_folder(self, folder_id):
        # Check lock status
        folder = self.data_manager.get_folder_by_id(folder_id)
        if folder and getattr(folder, 'is_locked', False):
            self.show_message(QMessageBox.Icon.Warning, "Locked", "This folder is locked and cannot be deleted.")
            return

        self.data_manager.delete_folder(folder_id)
        self.refresh_folders()
        
        # If deleted folder was active, clear everything
        if self.current_folder and self.current_folder.id == folder_id:
            self.current_folder = None
            self.current_note = None
            self.note_list.load_notes([])
            self.editor.clear()
            self.note_list.load_notes([])
            self.editor.clear()
            self.editor.editor.setReadOnly(True)
            self.editor_stack.setCurrentIndex(0) # Show Empty State
            self.whiteboard_widget.set_info(None, None) # Clear WB info
        
        # If deleted folder wasn't active, we don't need to do anything to the view
        elif not self.current_folder:
             # Ensure state key is clean
             pass

    def rename_folder(self, folder_id, new_name):
        """Handle folder rename request from sidebar."""
        # Check lock status
        folder = self.data_manager.get_folder_by_id(folder_id)
        if folder and getattr(folder, 'is_locked', False):
            self.show_message(QMessageBox.Icon.Warning, "Locked", "This folder is locked and cannot be renamed.")
            return

        success = self.data_manager.rename_folder(folder_id, new_name)
        if success:
            self.refresh_folders()
            # Maintain selection on the renamed folder
            self.sidebar.select_folder_by_id(new_name)  # ID becomes new name
        else:
            self.show_message(
                QMessageBox.Icon.Warning, 
                "Rename Failed",
                "Failed to rename folder. A folder with that name may already exist."
            )
        self.editor.clear()

    # --- Guards ---
    def check_lock(self):
        """Check if note is locked and warn the user."""
        if self.is_note_locked:
            QMessageBox.information(self, "Note Locked", "This note is locked. Please unlock it before switching or creating new items.")
            return True
        return False

    def toggle_note_lock(self, locked):
        self.is_note_locked = locked
        # Optionally disable editor or parts of sidebar?
        # For now, just blocking navigation is enough.

    def select_folder(self, folder_id):
        if self.check_lock(): return
        if folder_id == "ALL_NOTEBOOKS_ROOT":
            # Aggregate all notes from all non-archived folders
            all_notes = []
            for folder in self.data_manager.folders:
                if not getattr(folder, 'is_archived', False):
                    all_notes.extend(folder.notes)
            
            # Sort all notes by creation date (newest first)
            all_notes.sort(key=lambda n: n.created_at, reverse=True)
            
            self.current_folder = None
            self.note_list.load_notes(all_notes)
            self.current_note = None
            self.editor.clear()
            self.editor.editor.setReadOnly(True)
            
            # Save Selection
            self.data_manager.set_setting("last_selected_folder_id", "ALL_NOTEBOOKS_ROOT")
            
            self.whiteboard_widget.set_info("All Notebooks", None)
            # No whiteboard for aggregate view
            self.whiteboard_widget.clear()
            
            # Sync Sidebar Visually (if triggered from header)
            self.sidebar.select_folder_by_id("ALL_NOTEBOOKS_ROOT")
            return

        if folder_id == "RECENT_ROOT":
            # Smart View: Recent Notes
            recent_notes = self.data_manager.get_recent_notes()
            
            # Create Dummy Folder for Context
            self.current_folder = Folder("Recent", "RECENT_ROOT")
            self.current_folder.notes = recent_notes
            
            self.note_list.load_notes(recent_notes)
            self.current_note = None
            self.editor.clear()
            self.editor.editor.setReadOnly(True) # Keep ReadOnly until note selected
            
            self.whiteboard_widget.set_info("Recent Notes", None)
            self.whiteboard_widget.clear()
            return

        if folder_id == "TRASH_ROOT":
            # Smart View: Trash
            trash_notes = self.data_manager.get_trash_notes()
            
            self.current_folder = Folder("Trash", "TRASH_ROOT")
            self.current_folder.notes = trash_notes
            
            self.note_list.load_notes(trash_notes, folder_id="TRASH_ROOT")
            self.current_note = None
            self.editor.clear()
            self.editor.editor.setReadOnly(True)
            
            self.whiteboard_widget.set_info("Trash", None)
            self.whiteboard_widget.clear()
            return
            
        if folder_id == "ARCHIVED_ROOT":
            # Show all archived notes? Or just expand sidebar (already done)?
            # If clicked, let's show all archived notes across all notebooks logic?
            # Or just ignore if sidebar handles expansion.
            # Sidebar emits ARCHIVED_ROOT when header clicked?
            # Let's show all archived notes for consistency.
            all_archived = []
            for f in self.data_manager.folders:
                if getattr(f, 'is_archived', False):
                    all_archived.extend(f.notes)
            
            self.current_folder = Folder("Archived", "ARCHIVED_ROOT")
            self.current_folder.notes = all_archived
            self.note_list.load_notes(all_archived, folder_id="ARCHIVED_ROOT")
            self.current_note = None
            self.editor.clear()
            self.editor.editor.setReadOnly(True)
            self.whiteboard_widget.set_info("Archived", None)
            self.whiteboard_widget.clear()
            return

        self.current_folder = self.data_manager.get_folder_by_id(folder_id)
        if self.current_folder:
            self.note_list.load_notes(self.current_folder.notes, folder_id=folder_id)
            self.current_note = None
            self.editor.clear()
            
            # Disable editor until a note is selected
            self.editor.editor.setReadOnly(True)
            self.editor_stack.setCurrentIndex(0)

            # Restore View Mode
            view_mode = getattr(self.current_folder, 'view_mode', "list")
            self.note_list.set_view_mode(view_mode)
            
            # Save Selection
            self.data_manager.set_setting("last_selected_folder_id", folder_id)
            
            # Restore Last Used Note for this folder
            folders_meta = self.data_manager.get_setting("folders_meta", {})
            if folder_id in folders_meta:
                last_note_id = folders_meta[folder_id].get("last_note_id")
                if last_note_id:
                    # Verify note exists in current list
                    if any(n.id == last_note_id for n in self.current_folder.notes):
                         self.note_list.select_note_by_id(last_note_id)

            # Update Whiteboard Info (Clear Note Context)
            self.whiteboard_widget.set_info(self.current_folder.name, None)
            
            # Load Persistent Whiteboard for this folder
            # This ensures we see the correct board when switching folders
            try:
                wb_path = os.path.join(self.data_manager.get_folder_path(self.current_folder), "whiteboard.json")
                self.whiteboard_widget.load_file(wb_path)
            except Exception as e:
                logger.error(f"Error loading folder whiteboard: {e}")
    def delete_note(self, note_id):
        """Move note to trash."""
        if QMessageBox.question(self, "Move to Trash", "Move this note to Trash? You can restore it later.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.No:
            return

        if not self.current_folder:
            return

        # Check lock status
        note = self.current_folder.get_note_by_id(note_id)
        if note and getattr(note, 'is_locked', False):
            QMessageBox.warning(self, "Locked", "This note is locked and cannot be deleted.")
            return
            
        # If the deleted note was open, clear editor and close it
        if self.current_note and self.current_note.id == note_id:
            self.current_note = None
            self.editor.clear()
            self.editor_stack.setCurrentWidget(self.empty_state)
            self.metadata_bar.update_stats("", None)

        # Delete using DataManager
        self.data_manager.delete_note(self.current_folder, note_id)
        
        # Reload List
        self.note_list.load_notes(self.current_folder.notes, folder_id=self.current_folder.id)
        self.refresh_metadata()

    def restore_item(self, note_id, trash_path):
        """Restore note or folder from trash."""
        # Check if it was a folder
        success = False
        if os.path.isdir(trash_path):
            success = self.data_manager.restore_folder(trash_path)
        else:
            success = self.data_manager.restore_note(note_id, trash_path)
        
        if success:
            # Full refresh to update sidebar and note list
            self.refresh_folders()
            # If we were in Trash view, reload it
            if self.current_folder and self.current_folder.id == "TRASH_ROOT":
                self.select_folder("TRASH_ROOT")
        else:
            QMessageBox.warning(self, "Restore Failed", "Could not restore the item. The original location might be corrupted.")

    def permanent_delete_trash_item(self, trash_path):
        """Permanently remove an item from trash."""
        self.data_manager.permanent_delete_item(trash_path)
        # Reload Trash View
        if self.current_folder and self.current_folder.id == "TRASH_ROOT":
            self.select_folder("TRASH_ROOT")

    def empty_trash(self):
        """Permanently delete all items in trash (Phase 46.1)."""
        if QMessageBox.question(self, "Empty Trash", "Are you sure you want to permanently delete ALL items in the trash?\nThis action cannot be undone.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.No:
            return
            
        if self.data_manager.empty_trash():
            # Reload Trash View
            if self.current_folder and self.current_folder.id == "TRASH_ROOT":
                self.select_folder("TRASH_ROOT")
        else:
            QMessageBox.warning(self, "Failed", "Could not fully empty trash. Some files might be in use.")

    def clear_note_content(self, note_id):
        """Wipes all text content from a note."""
        # Find Note and its Folder
        target_note = None
        target_folder = None
        
        if self.current_folder:
            target_note = self.current_folder.get_note_by_id(note_id)
            target_folder = self.current_folder
            
        if not target_note:
            for folder in self.data_manager.folders:
                n = folder.get_note_by_id(note_id)
                if n:
                    target_note = n
                    target_folder = folder
                    break
                    
        if not target_note or not target_folder:
            return

        # Update note content
        target_note.content = ""
        # Save to disk
        self.data_manager.save_note(target_folder, target_note)
        
        # If it's the currently open note, update the UI
        if self.current_note and self.current_note.id == note_id:
            # Block auto-save temporarily to avoid saving the empty state back to itself redundantly
            # but editor.clear() is fine.
            self.editor.clear()
            self.refresh_metadata()
            
        logger.debug(f"Cleared content for note_id={note_id}")

    def rename_note(self, note_id, new_title):
        """Handle note rename request from note list."""
        if not self.current_folder:
            return
        
        success = self.data_manager.rename_note(self.current_folder.id, note_id, new_title)
        if success: 
            # Refresh note list to show new title
            self.note_list.load_notes(self.current_folder.notes)
            
            # If this was the currently open note, update title without reloading content
            if self.current_note and self.current_note.id == note_id:
                self.current_note.title = new_title
                # Block signals to prevent noteSelected from firing and reloading
                self.note_list.blockSignals(True)
                self.note_list.select_note_by_id(note_id)
                self.note_list.blockSignals(False)
            else:
                # For other notes, maintain selection normally
                self.note_list.select_note_by_id(note_id)
    
    def move_note_to_folder_with_dialog(self, note_id):
        """Show folder selection dialog and move note to selected folder."""
        if not self.current_folder:
            return
        
        # Identify the note object
        note = next((n for n in self.current_folder.notes if n.id == note_id), None)
        if not note:
            return

        # Prepare data for dialog
        all_folders = self.data_manager.folders
        
        # Show Custom Dialog
        dialog = MoveNoteDialog(self, [note], all_folders, self.current_folder.id)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if dialog.target_folder_id:
                self.move_note_to_folder(note_id, dialog.target_folder_id)
    
    def move_note_to_folder(self, note_id, target_folder_id):
        """Move a note from current folder to target folder."""
        if not self.current_folder:
            return
        
        from PyQt6.QtWidgets import QMessageBox
        
        # Get source and target folders
        source_folder = self.current_folder
        target_folder = self.data_manager.get_folder_by_id(target_folder_id)
        
        if not target_folder:
            QMessageBox.warning(self, "Error", "Target folder not found!")
            return
        
        if source_folder.id == target_folder.id:
            QMessageBox.information(self, "Same Folder", "The note is already in this folder!")
            return
        
        # Perform the move
        success = self.data_manager.move_note_between_folders(note_id, source_folder, target_folder)
        
        if success:
            # Clear editor if the moved note was currently selected
            if self.current_note and self.current_note.id == note_id:
                self.current_note = None
                self.editor.clear()
                self.editor_stack.setCurrentIndex(0)
            
            # Refresh source folder note list
            self.note_list.load_notes(source_folder.notes)
            
            # Show success message
            QMessageBox.information(
                self, 
                "Note Moved", 
                f"Note moved successfully to '{target_folder.name}'!"
            )
        else:
            QMessageBox.warning(self, "Error", "Failed to move note!")

    def create_note(self):
        if self.check_lock(): return
        folder = self.current_folder
        if not folder:
            active_folders = [f for f in self.data_manager.folders if not getattr(f, 'is_archived', False)]
            if not active_folders:
                self.show_message(QMessageBox.Icon.Warning, "No Folders", "Please create a folder first.")
                return
            
            # If in "All Notebooks" view, prompt for folder
            folder_names = [f.name for f in active_folders]
            name, ok = ZenItemDialog.getItem(self, "Select Folder", "Choose folder for new note:", folder_names, 0, False)
            if ok and name:
                folder = next(f for f in active_folders if f.name == name)
            else:
                return

        title, ok = ZenInputDialog.getText(self, "New Note", "Note Title:")
        if ok and title:
            new_note = Note(title=title)
            folder.add_note(new_note)
            self.data_manager.save_note(folder, new_note)
            
            # If we are in aggregate view, we need to reload all notes
            if not self.current_folder:
                 all_notes = []
                 for f in self.data_manager.folders:
                     if not getattr(f, 'is_archived', False):
                         all_notes.extend(f.notes)
                 all_notes.sort(key=lambda n: n.created_at, reverse=True)
                 self.note_list.load_notes(all_notes)
            else:
                 self.note_list.load_notes(folder.notes)
                 
            self.note_list.select_note_by_id(new_note.id)
            self.select_note(new_note.id)
    
    def reorder_note(self, note_id, new_position):
        """Handle note reordering request."""
        if not self.current_folder:
            return
        
        # Check lock status
        note = self.current_folder.get_note_by_id(note_id)
        if note and getattr(note, 'is_locked', False):
             # Allow reorder? Probably okay as it doesn't destroy content, but "move" implies structure change.
             # User said "don't allow to edit that and delte". Reordering is edge case.
             # Let's allow strictly visual reordering within same folder for now unless user complains.
             pass

        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            # Call data manager to reorder
            success = self.data_manager.reorder_note(self.current_folder.id, note_id, new_position)
            
            if success:
                # Reload note list to show new order
                self.note_list.load_notes(self.current_folder.notes)
                
                # Maintain selection on the reordered note
                self.note_list.select_note_by_id(note_id)
                
                # Update note index in editor if this is the current note
                if self.current_note and self.current_note.id == note_id:
                    from models.note import Note
                    sorted_notes = sorted(self.current_folder.notes, key=Note.sort_key)
                    try:
                        note_index = sorted_notes.index(self.current_note) + 1
                        self.editor.set_base_note_index(note_index)
                    except ValueError:
                        pass
        finally:
            QApplication.restoreOverrideCursor()
    
    def insert_note_at_position(self, target_position):
        """Insert a note at specific visual position in current list."""
        # Logic to calculate order value based on surrounding notes
        # ... (implementation needed if drag-drop reordering is strict)
        pass

    def open_note_by_id(self, note_id):
        """Handle request to open a specific note (e.g. from a link)."""
        print(f"DEBUG: MainWindow.open_note_by_id CALLED with note_id='{note_id}'")
        
        # 0. Store current note as origin before switching
        origin_note = self.current_note
        origin_id = origin_note.id if origin_note else None
        origin_title = origin_note.title if origin_note else "Previous Note"

        # 1. Find the note and its folder
        target_note = None
        target_folder = None
        
        for folder in self.data_manager.folders:
            for note in folder.notes:
                if note.id == note_id:
                    target_note = note
                    target_folder = folder
                    break
            if target_note:
                break
        
        if not target_note:
            print(f"DEBUG: Note {note_id} not found in data_manager")
            QMessageBox.warning(self, "Note Not Found", "The linked note likely has been deleted.")
            return

        print(f"DEBUG: Found note '{target_note.title}' in folder '{target_folder.name}'")

        # 2. Switch to Folder if needed
        if not self.current_folder or self.current_folder.id != target_folder.id:
            print(f"DEBUG: Switching to folder {target_folder.id}")
            # CALL SYNCHRONOUSLY to ensure note_list is populated BEFORE we try to select the note
            self.select_folder(target_folder.id)
            # Update Sidebar UI visually
            self.sidebar.select_folder_by_id(target_folder.id)

        # 3. Handle Archived/Active View in NoteList
        if hasattr(target_note, 'is_archived'):
            is_note_archived = target_note.is_archived
            if is_note_archived != self.note_list.showing_archived:
                print(f"DEBUG: Toggling archived view to {is_note_archived}")
                self.note_list.toggle_archived_view()

        # 4. Select Note
        print(f"DEBUG: Selecting note {note_id} in NoteList")
        self._navigating_via_link = True # Prevention flag for select_note
        self.note_list.select_note_by_id(note_id)
        
        # 5. Show back button if we moved to a DIFFERENT note
        if origin_id and origin_id != note_id:
            print(f"DEBUG: Showing Back Button to return to {origin_id}")
            self.editor.show_back_button(origin_id, origin_title)

    def open_note_overlay(self, note_id):
        """Open a note in a separate overlay window."""
        logger.debug(f"MainWindow.open_note_overlay CALLED: note_id='{note_id}'")
        note = self.data_manager.get_note_by_id(note_id)
        if not note:
            QMessageBox.warning(self, "Note Not Found", "The requested note could not be found.")
            return
            
        overlay = NoteOverlayDialog(note.id, note.title, note.content, self.data_manager, self)
        overlay.show()
        
        # Keep a reference to prevent garbage collection if needed
        if not hasattr(self, '_overlays'):
            self._overlays = []
        self._overlays.append(overlay)
        # Clean up reference on close
        overlay.finished.connect(lambda: self._overlays.remove(overlay) if overlay in self._overlays else None)
        # Load Content
        self.select_note(note_id)

    def select_note(self, note_id):
        if self.check_lock():
            # Restore selection in list if it changed
            if self.current_note:
                self.note_list.select_note_by_id(self.current_note.id)
            return
        # Hide navigation back button if we are switching normally (sidebar/list click)
        if not getattr(self, '_navigating_via_link', False):
             self.editor.hide_back_button()
        self._navigating_via_link = False
        
        # SAVE PREVIOUS STATE
        if self.current_note:
            # Save scroll position
            scroll_val = self.editor.editor.verticalScrollBar().value()
            self.current_note.last_scroll_position = scroll_val
            
            # Save splitter sizes (NESTED content splitter)
            self.current_note.content_splitter_sizes = self.content_splitter.sizes()
            
            # If auto-save timer is running, force save now
            if self.save_timer.isActive():
                self.save_timer.stop()
                self._perform_save()

        # Find Note and its Folder
        target_note = None
        target_folder = None
        
        if self.current_folder:
            target_note = self.current_folder.get_note_by_id(note_id)
            target_folder = self.current_folder
        else:
            # Aggregate view: Find which folder this note belongs to
            for folder in self.data_manager.folders:
                n = folder.get_note_by_id(note_id)
                if n:
                    target_note = n
                    target_folder = folder
                    break
        
        if not target_note:
            return

        self.current_note = target_note

        # Update Last Opened
        if self.current_note:
            self.current_note.last_opened = datetime.now().isoformat()
            # We should save this change, but maybe debounce it? 
            # Or just save immediately effectively as it's metadata.
            # However, _perform_save saves content. Let's use data_manager.save_note explicitly if needed,
            # but _perform_save acts on current_note.
            # To avoid saving content unnecessarily, we just update the object. 
            # It will be saved on next content save OR we can trigger a metadata save.
            # Let's trigger a save to ensure it persists even if no content edit.
            if self.current_folder:
                 self.data_manager.save_note(self.current_folder, self.current_note)

        # Refine target_folder for Recent/Trash views (if they have parent ref)
        if self.current_folder and self.current_folder.id in ["RECENT_ROOT", "TRASH_ROOT"] and hasattr(target_note, '_parent_folder'):
             target_folder = target_note._parent_folder
        
        # Check folder context for ReadOnly
        force_readonly = False
        if self.current_folder:
             # Check Special Roots
             if self.current_folder.id in ["TRASH_ROOT", "ARCHIVED_ROOT"]:
                 force_readonly = True
             # Check Normal Archived Folders
             elif getattr(self.current_folder, 'is_archived', False):
                 force_readonly = True
        
        # Enable editor for typing ONLY if not locked
        is_locked = getattr(self.current_note, 'is_locked', False)
        self.editor.editor.setReadOnly(is_locked or force_readonly)
        self.editor_stack.setCurrentIndex(1) # Show Editor
        
        # Update window title or status to indicate lock?
        if is_locked:
            self.statusBar().showMessage(f"Note '{self.current_note.title}' is locked. Unlock to edit.", 3000)
        
        # Set context in editor for image storage
        self.editor.set_current_folder(target_folder)
        # Load note content with sidecar images
        self.editor.set_html(self.current_note.content, self.current_note.whiteboard_images)
        
        # Calculate note's 1-based index for level numbering
        from models.note import Note
        sorted_notes = sorted(target_folder.notes, key=Note.sort_key)
        try:
            note_index = sorted_notes.index(self.current_note) + 1  # 1-based
            self.editor.set_base_note_index(note_index)
        except ValueError:
            self.editor.set_base_note_index(1)  # Fallback
        
        # Persist as Last Used Note for this folder
        self.data_manager.update_folder_last_note(target_folder.id, note_id)
        
        # Update Whiteboard Info with Note Name
        # Update Whiteboard Info with Note Name
        self.whiteboard_widget.set_info(target_folder.name, self.current_note.title)
        
        # RESTORE SCROLL POSITION & SPLITTER SIZES
        # Use QTimer to allow layout/content to be fully set
        QTimer.singleShot(100, lambda: self._restore_note_layout())

    def _restore_note_layout(self):
        if not self.current_note: return
        
        # Restore Splitter Sizes
        if getattr(self.current_note, 'content_splitter_sizes', None):
            self.content_splitter.setSizes(self.current_note.content_splitter_sizes)
            
        # Restore Scroll Position
        pos = getattr(self.current_note, 'last_scroll_position', 0)
        self.editor.editor.verticalScrollBar().setValue(pos)

    def _restore_scroll_position(self):
        # Keep for backward compatibility or if called elsewhere
        if self.current_note:
            pos = getattr(self.current_note, 'last_scroll_position', 0)
            self.editor.editor.verticalScrollBar().setValue(pos)

    def auto_save_note(self):
        """Trigger a debounced save."""
        self.save_timer.start()

    def _perform_save(self):
        """Actually write to disk."""
        if getattr(self, '_is_saving', False): return
        self._is_saving = True
        
        try:
            if self.current_folder and self.current_note:
                self.current_note.content = self.editor.get_html()
                self.current_note.whiteboard_images = self.editor.get_whiteboard_images()
                
                # Capture scroll and splitter position during save too
                self.current_note.last_scroll_position = self.editor.editor.verticalScrollBar().value()
                self.current_note.content_splitter_sizes = self.content_splitter.sizes()
                
                target_folder = self.current_folder
                if self.current_folder.id == "RECENT_ROOT" and hasattr(self.current_note, '_parent_folder'):
                     target_folder = self.current_note._parent_folder
                
                self.data_manager.save_note(target_folder, self.current_note)
                
                # Live Update Highlight Preview
                self.refresh_highlight_preview_if_visible()
                
                # Visual Indicator (Requested UX)
                self.statusBar().showMessage("Saved", 1000)
        except Exception as e:
            logger.error(f"Error in _perform_save", exc_info=True)
        finally:
            self._is_saving = False
    
    def _handle_splitter_resize(self, pos, index):
        """Handle main splitter resize event to track drawer state."""
        if not hasattr(self, 'main_splitter'): return
        
        sizes = self.main_splitter.sizes()
        if len(sizes) >= 2:
            list_w = sizes[1]
            if list_w > 0:
                self._last_note_list_width = list_w
        
        # Original scaling logic (if any)
        if hasattr(self.editor, 'on_parent_resize'):
            self.editor.on_parent_resize()

    def closeEvent(self, event):
        """Ensure data is saved before closing."""
        if self.save_timer.isActive():
            self.save_timer.stop()
            self._perform_save()
        
        # Save whiteboard if visible
        if hasattr(self, 'whiteboard_widget') and self.whiteboard_widget.isVisible():
            self.auto_save_whiteboard()
        
        # Cleanup child components
        if hasattr(self, 'editor'):
            self.editor.cleanup()
            
        super().closeEvent(event)


    def save_current_note(self):
        # Force immediate save
        if self.save_timer.isActive():
            self.save_timer.stop()
        self._perform_save()
        
        # Visual feedback could be added here (e.g., status bar)
        self.statusBar().showMessage("Saved", 2000)

    def export_folder_by_id(self, folder_id):
        folder = self.data_manager.get_folder_by_id(folder_id)
        if not folder:
            return
        
        # Show theme selection dialog first
        theme_choice = self.show_pdf_theme_dialog()
        if theme_choice == -1:  # Cancelled
            return
        
        from pdf_export.exporter import export_folder_to_pdf
        import os
        
        # Determine initial directory
        last_dir = self.data_manager.get_setting("last_export_dir")
        if not last_dir or not os.path.exists(last_dir):
            last_dir = os.path.expanduser("~/Documents")
            
        # Default filename
        filename = f"{folder.name}_Full_Export.pdf"
        filename = "".join([c for c in filename if c.isalpha() or c.isdigit() or c==' ' or c=='.']).rstrip()
        
        default_path = os.path.join(last_dir, filename)

        # Ask User
        path, _ = QFileDialog.getSaveFileName(self, "Export Folder to PDF", default_path, "PDF Files (*.pdf)")
        
        if not path:
            return # Cancelled

        # Save new location
        new_dir = os.path.dirname(path)
        self.data_manager.set_setting("last_export_dir", new_dir)

        # Progress Dialog for folder export
        theme_name = "Light" if theme_choice == 0 else "Dark"
        progress = QProgressDialog(f"Exporting Folder '{folder.name}' ({theme_name} Theme)...", "Cancel", 0, 100, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0) # Show immediately
        progress.setValue(0)
        
        def update_folder_progress(current, total):
            if progress.wasCanceled():
                return
            progress.setMaximum(total)
            progress.setLabelText(f"Exporting Page {current} of {total}...")
            progress.setValue(current)

        try:
            export_folder_to_pdf(folder, path, progress_callback=update_folder_progress, theme=theme_choice)
            
            if not progress.wasCanceled():
                progress.setValue(progress.maximum())
                self.show_message(QMessageBox.Icon.Information, "Export Successful", f"Folder exported to:\n{path}")
            else:
                self.show_message(QMessageBox.Icon.Warning, "Export Cancelled", "Export operation was cancelled.")
        except Exception as e:
            if not progress.wasCanceled():
                self.show_message(QMessageBox.Icon.Critical, "Export Error", f"Failed to export PDF:\n{e}")
        finally:
            progress.close()

    def export_folder_whiteboard(self, folder_id):
        """Export the whiteboard.json of the folder to a PDF."""
        folder = self.data_manager.get_folder_by_id(folder_id)
        if not folder:
            return

        # Check if whiteboard.json exists
        wb_path = os.path.join(self.data_manager.get_folder_path(folder), "whiteboard.json")
        if not os.path.exists(wb_path):
            self.show_message(QMessageBox.Icon.Warning, "No Whiteboard", "This folder does not have a whiteboard yet.")
            return

        # Show theme selection dialog first
        theme_choice = self.show_pdf_theme_dialog()
        if theme_choice == -1:  # Cancelled
            return

        from pdf_export.export_whiteboard import export_whiteboard_to_pdf
        
        # Determine initial directory
        last_dir = self.data_manager.get_setting("last_export_dir")
        if not last_dir or not os.path.exists(last_dir):
            last_dir = os.path.expanduser("~/Documents")
            
        # Default filename
        filename = f"{folder.name}_Whiteboard.pdf"
        filename = "".join([c for c in filename if c.isalpha() or c.isdigit() or c==' ' or c=='.']).rstrip()
        
        default_path = os.path.join(last_dir, filename)

        # Ask User
        path, _ = QFileDialog.getSaveFileName(self, "Export Whiteboard to PDF", default_path, "PDF Files (*.pdf)")
        
        if not path:
            return # Cancelled

        # Save new location
        new_dir = os.path.dirname(path)
        self.data_manager.set_setting("last_export_dir", new_dir)

        # Progress Dialog
        theme_name = "Light" if theme_choice == 0 else "Dark"
        progress = QProgressDialog(f"Exporting Whiteboard for '{folder.name}' ({theme_name} Theme)...", "Cancel", 0, 0, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        progress.show()
        QApplication.processEvents()
        
        try:
            success = export_whiteboard_to_pdf(wb_path, path, parent=self, theme=theme_choice)
            
            progress.close()
            
            if success:
                self.show_message(QMessageBox.Icon.Information, "Export Successful", f"Whiteboard exported to:\n{path}")
            else:
                self.show_message(QMessageBox.Icon.Warning, "Export Failed", "Failed to export whiteboard.")
        except Exception as e:
            progress.close()
            self.show_message(QMessageBox.Icon.Critical, "Export Error", f"Failed to export PDF:\n{e}")

    def export_note_by_id_word(self, note_id):
        """Handle export request from context menu for Word."""
        if not self.current_folder: return
        note = next((n for n in self.current_folder.notes if n.id == note_id), None)
        if not note: return
        
        default_name = f"{note.title}.docx"
        last_dir = self.data_manager.get_setting("last_export_dir", os.path.expanduser("~/Documents"))
        default_path = os.path.join(last_dir, default_name)
        
        path, _ = QFileDialog.getSaveFileName(self, "Export Note to Word", default_path, "Word Documents (*.docx)")
        if not path: return
        
        new_dir = os.path.dirname(path)
        self.data_manager.set_setting("last_export_dir", new_dir)
        
        try:
            success = export_note_to_docx(note, path)
            if success:
                 self.show_message(QMessageBox.Icon.Information, "Export Successful", f"Note exported to:\n{path}")
            else:
                 self.show_message(QMessageBox.Icon.Warning, "Export Failed", "Could not export note.")
        except Exception as e:
            self.show_message(QMessageBox.Icon.Critical, "Export Error", f"Failed to export Word doc:\n{e}")

    def export_pdf(self):
        # Legacy method if needed, but we mostly use by ID now
        if self.current_folder:
            self.export_folder_by_id(self.current_folder.id)

    def show_pdf_theme_dialog(self):
        """Show dialog to select PDF export theme."""
        dialog = QDialog(self)
        dialog.setWindowTitle("PDF Export Theme")
        dialog.setWindowModality(Qt.WindowModality.WindowModal)
        dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        dialog.setMinimumWidth(350)
        
        layout = QVBoxLayout(dialog)
        
        # Title
        title_label = QLabel("Choose PDF Theme:")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Theme options
        theme_group = QButtonGroup()
        
        light_radio = QRadioButton("Light Theme (White Background)")
        light_radio.setChecked(True)  # Default
        light_radio.setStyleSheet("font-size: 12px; padding: 5px;")
        theme_group.addButton(light_radio, 0)
        
        layout.addWidget(light_radio)
        
        dark_radio = QRadioButton("Dark Theme (Dark Background)")
        dark_radio.setStyleSheet("font-size: 12px; padding: 5px;")
        theme_group.addButton(dark_radio, 1)
        layout.addWidget(dark_radio)
        
        btn_box = QHBoxLayout()
        export_btn = QPushButton("Export")
        export_btn.clicked.connect(dialog.accept)
        btn_box.addStretch()
        btn_box.addWidget(export_btn)
        layout.addLayout(btn_box)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return theme_group.checkedId()
        return 0

    def export_current_note_word(self):
        """Export current note to Word (.docx)."""
        if not self.current_note: return
        
        default_name = f"{self.current_note.title}.docx"
        last_dir = self.data_manager.get_setting("last_export_dir", os.path.expanduser("~/Documents"))
        default_path = os.path.join(last_dir, default_name)
        
        path, _ = QFileDialog.getSaveFileName(self, "Export Note to Word", default_path, "Word Documents (*.docx)")
        if not path: return
        
        new_dir = os.path.dirname(path)
        self.data_manager.set_setting("last_export_dir", new_dir)
        
        try:
            success = export_note_to_docx(self.current_note, path)
            if success:
                 self.show_message(QMessageBox.Icon.Information, "Export Successful", f"Note exported to:\n{path}")
            else:
                 self.show_message(QMessageBox.Icon.Warning, "Export Failed", "Could not export note.")
        except Exception as e:
            self.show_message(QMessageBox.Icon.Critical, "Export Error", f"Failed to export Word doc:\n{e}")

    def export_folder_word(self, folder_id):
        """Export folder to Word (.docx)."""
        folder = self.data_manager.get_folder_by_id(folder_id)
        if not folder: return
        
        default_name = f"{folder.name}_Export.docx"
        last_dir = self.data_manager.get_setting("last_export_dir", os.path.expanduser("~/Documents"))
        default_path = os.path.join(last_dir, default_name)
        
        path, _ = QFileDialog.getSaveFileName(self, "Export Folder to Word", default_path, "Word Documents (*.docx)")
        if not path: return
        
        new_dir = os.path.dirname(path)
        self.data_manager.set_setting("last_export_dir", new_dir)
        
        progress = QProgressDialog(f"Exporting '{folder.name}' to Word...", "Cancel", 0, len(folder.notes), self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.show()
        
        def update_progress(current, total):
            progress.setValue(current)
            if progress.wasCanceled():
                raise Exception("Export canceled by user")
        
        try:
            success = export_folder_to_docx(folder, path, progress_callback=update_progress)
            progress.close()
            if success:
                 self.show_message(QMessageBox.Icon.Information, "Export Successful", f"Folder exported to:\n{path}")
        except Exception as e:
            progress.close()
            self.show_message(QMessageBox.Icon.Critical, "Export Error", f"Failed to export Word doc:\n{e}")

    def export_current_note_pdf(self):
        if not self.current_note:
            self.show_message(QMessageBox.Icon.Warning, "No Note", "Please select a note to export.")
            return

        # Show theme selection dialog first
        theme_choice = self.show_pdf_theme_dialog()
        if theme_choice == -1:  # Cancelled
            return

        from pdf_export.exporter import export_note_to_pdf
        from PyQt6.QtWidgets import QProgressDialog, QApplication
        import os

        # Determine initial directory
        last_dir = self.data_manager.get_setting("last_export_dir")
        if not last_dir or not os.path.exists(last_dir):
            last_dir = os.path.expanduser("~/Documents")

        filename = f"{self.current_note.title}.pdf"
        # Sanitize
        filename = "".join([c for c in filename if c.isalpha() or c.isdigit() or c==' ' or c=='.']).rstrip()
        
        default_path = os.path.join(last_dir, filename)

        # Ask User
        path, _ = QFileDialog.getSaveFileName(self, "Export Note to PDF", default_path, "PDF Files (*.pdf)")
        
        if not path:
            return # Cancelled

        # Save new location
        new_dir = os.path.dirname(path)
        self.data_manager.set_setting("last_export_dir", new_dir)
        
        # Progress Dialog
        theme_name = "Light" if theme_choice == 0 else "Dark"
        progress = QProgressDialog(f"Exporting Note '{self.current_note.title}' ({theme_name} Theme)...", "Cancel", 0, 100, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0) # Show immediately
        progress.setValue(0)
        
        def update_note_progress(current, total):
            if progress.wasCanceled():
                return
            progress.setMaximum(total)
            progress.setLabelText(f"Exporting Page {current} of {total}...")
            progress.setValue(current)


        try:
            # CRITICAL: Save note before exporting to ensure whiteboard_images are current
            self._perform_save()
            
            export_note_to_pdf(self.current_note, path, progress_callback=update_note_progress, theme=theme_choice)
           
            if not progress.wasCanceled():
                progress.setValue(progress.maximum())
                self.show_message(QMessageBox.Icon.Information, "Export Successful", f"Note exported to:\n{path}")
            else:
                self.show_message(QMessageBox.Icon.Warning, "Export Cancelled", "Export operation was cancelled.")
        except Exception as e:
            if not progress.wasCanceled():
                self.show_message(QMessageBox.Icon.Critical, "Export Error", f"Failed to export PDF:\n{e}")
        finally:
            progress.close()

    def export_note_by_id(self, note_id):
        """Handle export request from context menu."""
        if not self.current_folder: return
        
        note = next((n for n in self.current_folder.notes if n.id == note_id), None)
        if not note: return
        
        # We can reuse the logic. If the requested note is CURRENT, use main method
        # If not, temporarily set current note? No, safer to duplicate logic slightly to avoid side effects
        
        # Show theme selection dialog first
        theme_choice = self.show_pdf_theme_dialog()
        if theme_choice == -1:  # Cancelled
            return

        from pdf_export.exporter import export_note_to_pdf
        from PyQt6.QtWidgets import QProgressDialog
        import os

        # Determine initial directory
        last_dir = self.data_manager.get_setting("last_export_dir")
        if not last_dir or not os.path.exists(last_dir):
            last_dir = os.path.expanduser("~/Documents")

        filename = f"{note.title}.pdf"
        # Sanitize
        filename = "".join([c for c in filename if c.isalpha() or c.isdigit() or c==' ' or c=='.']).rstrip()
        
        default_path = os.path.join(last_dir, filename)

        # Ask User
        path, _ = QFileDialog.getSaveFileName(self, "Export Note to PDF", default_path, "PDF Files (*.pdf)")
        
        if not path:
            return # Cancelled

        # Save new location
        new_dir = os.path.dirname(path)
        self.data_manager.set_setting("last_export_dir", new_dir)
        
        # Progress Dialog
        theme_name = "Light" if theme_choice == 0 else "Dark"
        progress = QProgressDialog(f"Exporting Note '{note.title}' ({theme_name} Theme)...", "Cancel", 0, 100, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0) # Show immediately
        progress.setValue(0)
        
        def update_note_progress(current, total):
            if progress.wasCanceled():
                return
            progress.setMaximum(total)
            progress.setLabelText(f"Exporting Page {current} of {total}...")
            progress.setValue(current)

        try:
            export_note_to_pdf(note, path, progress_callback=update_note_progress, theme=theme_choice)
            
            if not progress.wasCanceled():
                progress.setValue(progress.maximum())
                self.show_message(QMessageBox.Icon.Information, "Export Successful", f"Note exported to:\n{path}")
            else:
                self.show_message(QMessageBox.Icon.Warning, "Export Cancelled", "Export operation was cancelled.")
        except Exception as e:
            if not progress.wasCanceled():
                self.show_message(QMessageBox.Icon.Critical, "Export Error", f"Failed to export PDF:\n{e}")
        finally:
            progress.close()

    def preview_note_by_id(self, note_id):
        """Handle preview request from context menu using Virtual Folder."""
        if not self.current_folder: return
        
        note = next((n for n in self.current_folder.notes if n.id == note_id), None)
        if not note: return
        
        from types import SimpleNamespace
        # Create a Virtual Folder that looks like a Folder object to the Exporter
        virtual_folder = SimpleNamespace(
            id=f"virtual_{note.id}",
            name=note.title, # Title of window will be note title
            notes=[note],
            is_pinned=False,
            priority=0,
            created_at=note.created_at # Inherit date
        )
        
        from ui.preview_dialog import PDFPreviewDialog
        
        # Collect whiteboard images for just this note
        wb_images = getattr(note, 'whiteboard_images', {})
        
        current_theme_mode = self.data_manager.get_setting("theme_mode", "light")
        
        # Calculate correct note index for numbering
        start_index = 1
        try:
            from models.note import Note
            sorted_notes = sorted(self.current_folder.notes, key=Note.sort_key)
            for i, n in enumerate(sorted_notes, 1):
                if n.id == note.id:
                    start_index = i
                    break
        except Exception as e:
            print(f"Error calculating note index: {e}")

        try:
            dialog = PDFPreviewDialog(virtual_folder, wb_images, self, current_theme_mode, start_index=start_index)
            
            # Handle export from preview dialog
            def on_export_confirmed(theme_choice):
                # If user clicks Export in preview, we redirect to the single file export logic
                # Use the SAME path selection logic as export_note_by_id
                
                # Determine initial directory
                last_dir = self.data_manager.get_setting("last_export_dir")
                if not last_dir or not os.path.exists(last_dir):
                    last_dir = os.path.expanduser("~/Documents")

                filename = f"{note.title}.pdf"
                filename = "".join([c for c in filename if c.isalpha() or c.isdigit() or c==' ' or c=='.']).rstrip()
                default_path = os.path.join(last_dir, filename)

                # Ask User
                path, _ = QFileDialog.getSaveFileName(self, "Export Note to PDF", default_path, "PDF Files (*.pdf)")
                
                if not path: return 

                new_dir = os.path.dirname(path)
                self.data_manager.set_setting("last_export_dir", new_dir)
                
                # Run Export
                from pdf_export.exporter import export_note_to_pdf
                theme_name = "Light" if theme_choice == 0 else "Dark"
                progress = QProgressDialog(f"Exporting Note '{note.title}' ({theme_name} Theme)...", "Cancel", 0, 100, self)
                progress.setWindowModality(Qt.WindowModality.WindowModal)
                progress.setMinimumDuration(0)
                progress.setValue(0)
                
                def update_note_progress(current, total):
                    if progress.wasCanceled(): return
                    progress.setMaximum(total)
                    progress.setLabelText(f"Exporting Page {current} of {total}...")
                    progress.setValue(current)


                try:
                    # CRITICAL: Save if exporting current note to ensure whiteboard_images are current
                    if note == self.current_note:
                        self._perform_save()
                    
                    export_note_to_pdf(note, path, progress_callback=update_note_progress, theme=theme_choice)
                    if not progress.wasCanceled():
                        progress.setValue(progress.maximum())
                        self.show_message(QMessageBox.Icon.Information, "Export Successful", f"Note exported to:\n{path}")
                except Exception as e:
                    if not progress.wasCanceled():
                        self.show_message(QMessageBox.Icon.Critical, "Export Error", f"Failed to export PDF:\n{e}")
                finally:
                    progress.close()

            dialog.exportConfirmed.connect(on_export_confirmed)
            dialog.exec()
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.show_message(QMessageBox.Icon.Critical, "Preview Error", f"An error occurred while opening preview:\n{e}")


    def show_pdf_preview(self):
        if not self.current_folder:
            self.show_message(QMessageBox.Icon.Warning, "No Folder", "Please select a folder to preview.")
            return

        from pdf_export.exporter import generate_folder_html, process_images_for_pdf, apply_theme_to_html
        from ui.preview_dialog import PDFPreviewDialog
        
        # Generate HTML with performance optimizations
        try:
            # Aggregate all images first
            all_whiteboard_images = {}
            for note in self.current_folder.notes:
                wb_imgs = getattr(note, 'whiteboard_images', {})
                all_whiteboard_images.update(wb_imgs)
            
            # Get current theme mode
            current_theme_mode = self.data_manager.get_setting("theme_mode", "light")
            
            # Show Dialog with theme selection
            dialog = PDFPreviewDialog(self.current_folder, all_whiteboard_images, self, current_theme_mode=current_theme_mode)
            
            # Connect Export button from dialog to actual export function with selected theme
            dialog.exportConfirmed.connect(lambda theme: self.export_folder_by_id_with_theme(self.current_folder.id, theme))
            
            dialog.exec()
            
        except Exception as e:
            self.show_message(QMessageBox.Icon.Critical, "Preview Error", f"Failed to generate preview:\n{e}")

    def show_shortcut_dialog(self):
        """Show the shortcut configuration dialog."""
        dialog = ShortcutDialog(self.shortcut_manager, self)
        
        def on_saved():
            # Refresh Global Shortcuts
            self.action_new_note.setShortcut(self.shortcut_manager.get_shortcut("global_new_note"))
            self.action_new_folder.setShortcut(self.shortcut_manager.get_shortcut("global_new_folder"))
            self.action_save.setShortcut(self.shortcut_manager.get_shortcut("global_save"))
            self.action_theme.setShortcut(self.shortcut_manager.get_shortcut("global_toggle_theme"))
            self.action_highlight_prev.setShortcut(self.shortcut_manager.get_shortcut("global_highlight_preview"))
            self.action_pdf_prev.setShortcut(self.shortcut_manager.get_shortcut("global_pdf_preview"))
            
            # Note: Editor toolbar shortcuts update automatically on use/hover (since they check manager)
            # But the displayed shortcut in ToolTip is generated at init.
            # To be perfect, we should signal Editor to refresh tooltips.
            if hasattr(self, 'editor') and hasattr(self.editor, 'setup_toolbar'):
                 # Re-run setup_toolbar? No, that duplicates actions.
                 # Better to have a refresh method in editor.
                 # For now, Global actions are the critical ones.
                 pass

        dialog.saved.connect(on_saved)
        dialog.exec()
    
    def export_folder_by_id_with_theme(self, folder_id, theme_choice):
        """Export folder with a pre-selected theme (called from preview dialog)."""
        folder = self.data_manager.get_folder_by_id(folder_id)
        if not folder:
            return
        
        from pdf_export.exporter import export_folder_to_pdf
        import os
        
        # Determine initial directory
        last_dir = self.data_manager.get_setting("last_export_dir")
        if not last_dir or not os.path.exists(last_dir):
            last_dir = os.path.expanduser("~/Documents")
            
        # Default filename
        filename = f"{folder.name}_Full_Export.pdf"
        filename = "".join([c for c in filename if c.isalpha() or c.isdigit() or c==' ' or c=='.']).rstrip()
        
        default_path = os.path.join(last_dir, filename)

        # Ask User for save location
        path, _ = QFileDialog.getSaveFileName(self, "Export Folder to PDF", default_path, "PDF Files (*.pdf)")
        
        if not path:
            return # Cancelled

        # Save new location
        new_dir = os.path.dirname(path)
        self.data_manager.set_setting("last_export_dir", new_dir)

        # Progress Dialog for folder export
        theme_name = "Light" if theme_choice == 0 else "Dark"
        progress = QProgressDialog(f"Exporting Folder '{folder.name}' ({theme_name} Theme)...", "Cancel", 0, 100, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0) # Show immediately
        progress.setValue(0)
        
        def update_folder_progress(current, total):
            if progress.wasCanceled():
                return
            progress.setMaximum(total)
            progress.setLabelText(f"Exporting Page {current} of {total}...")
            progress.setValue(current)

        try:
            export_folder_to_pdf(folder, path, progress_callback=update_folder_progress, theme=theme_choice)
            
            if not progress.wasCanceled():
                progress.setValue(progress.maximum())
                self.show_message(QMessageBox.Icon.Information, "Export Successful", f"Folder exported to:\n{path}")
            else:
                self.show_message(QMessageBox.Icon.Warning, "Export Cancelled", "Export operation was cancelled.")
        except Exception as e:
            if not progress.wasCanceled():
                self.show_message(QMessageBox.Icon.Critical, "Export Error", f"Failed to export PDF:\n{e}")
        finally:
            progress.close()



    def export_current_highlights(self):
        """Re-extract and export highlights"""
        if not self.current_folder: return
        grouped, count = self._extract_highlights(self.current_folder.notes)
        if grouped:
            self._export_highlights_pdf(grouped, count)

    def show_highlight_preview(self):
        """Show preview of all highlighted and underlined text in Split View (Full Width)"""
        # Toggle: If visible, hide it and restore sidebar/list
        if hasattr(self, 'highlight_view') and self.highlight_view.isVisible():
            self.highlight_view.setVisible(False)
            self.sidebar.setVisible(True)
            self.note_list.setVisible(True)
            return

        if not self.current_folder:
            self.show_message(QMessageBox.Icon.Warning, "No Folder", "Please select a folder to preview highlights.")
            return

        # Extract highlights
        # SORT NOTES: Using 'order' if available, else 'updated_at' or 'id'
        # Assuming notes have an 'order' attribute from database
        try:
             sorted_notes = sorted(self.current_folder.notes, key=lambda n: n.order)
        except:
             # Fallback if order is missing
             sorted_notes = self.current_folder.notes
        
        # Sync Content: Ensure the currently open note is up-to-date in the list
        if self.current_note:
            current_html = self.editor.get_html()
            # Update the object in the list
            for note in sorted_notes:
                if note.id == self.current_note.id:
                    note.content = current_html
                    break
             
        grouped_highlights, total_count = self._extract_highlights(sorted_notes)
        
        if not grouped_highlights:
            # Allow empty state
            pass
        
        # Generate HTML
        html_content = self._generate_highlight_preview_html(grouped_highlights, total_count)
        self.highlight_view.setHtml(html_content)
        
        # Ensure links are captured (Fix for buttons not working)
        self.highlight_view.setOpenLinks(False) 
        
        # Hide whiteboard widget if it's open (mutually exclusive)
        if self.whiteboard_widget.isVisible():
            self.whiteboard_widget.setVisible(False)
        
        # Show Split View (on the LEFT of Editor)
        self.highlight_view.setVisible(True)
        # Hide Sidebar and List for 50/50 Focus
        self.sidebar.setVisible(False)
        self.note_list.setVisible(False)
        
        # Set 50/50 split for [highlight_view, whiteboard_placeholder (hidden), editor]
        total_width = self.width()
        self.content_splitter.setSizes([total_width // 2, 0, total_width // 2])

    def show_whiteboard_split_view(self):
        """Show whiteboard in Split View - embedded like Highlight Preview"""
        
        # Toggle: If whiteboard widget is visible, hide it and restore sidebar/list
        if self.whiteboard_widget.isVisible():
            self.whiteboard_widget.setVisible(False)
            self.sidebar.setVisible(True)
            self.note_list.setVisible(True)
            return

        if not self.current_folder:
            self.show_message(QMessageBox.Icon.Warning, "No Folder", "Please select a folder to use whiteboard.")
            return

        # Hide highlight view if it's open (mutually exclusive)
        if self.highlight_view.isVisible():
            self.highlight_view.setVisible(False)

        # Hide Sidebar and Note List for split view (EXACTLY like Highlight Preview)
        self.sidebar.setVisible(False)
        self.note_list.setVisible(False)

        # Load folder-specific whiteboard file
        folder_path = self.data_manager.get_folder_path(self.current_folder)
        if folder_path:
            wb_path = os.path.join(folder_path, "whiteboard.json")
            self.whiteboard_widget.load_file(wb_path)
            
            # Set Info with Note Name if available
            note_name = self.current_note.title if self.current_note else None
            self.whiteboard_widget.set_info(self.current_folder.name, note_name)

        # Show Whiteboard Widget (embedded in splitter)
        self.whiteboard_widget.setVisible(True)
        
        # Set 50/50 split (highlight hidden=0, whiteboard 50%, editor 50%)
        total_width = self.width()
        # Sizes: [highlight_view (hidden=0), whiteboard_widget (50%), editor (50%)]
        self.content_splitter.setSizes([0, total_width // 2, total_width // 2])

    def on_whiteboard_closed(self):
        """Handle whiteboard close event - Restore default view"""
        if self.whiteboard_widget.isVisible():
            self.whiteboard_widget.setVisible(False)
            
            # Clear editing state so next regular insert is new
            self.editing_image_id = None
            
            # Restore Sidebar and Note List
            self.sidebar.setVisible(True)
            self.note_list.setVisible(True)
            
            # Reset Splitter: [Sidebar(150), NoteList(250), Editor(Rest)]
            # Since we collapsed them to 0 in jump_to_whiteboard, we MUST restore sizes explicitly
            main_splitter = self.centralWidget()
            if isinstance(main_splitter, QSplitter):
                current_total = main_splitter.width()
                # Restore to default proportions
                main_splitter.setSizes([150, 250, current_total - 400])
            
            # For the INNER content splitter (Highlight/Whiteboard/Editor)
            # Ensure Editor takes full width of that section
            total_width = self.width()
            h_view_size = self.content_splitter.sizes()[0]
            self.content_splitter.setSizes([h_view_size, 0, total_width]) 

    def auto_save_whiteboard(self):
        """Auto-save whiteboard when content changes"""
        # 1. Prioritize saving to the specifically loaded file (e.g. during cross-folder edit)
        if self.whiteboard_widget.active_file_path:
             self.whiteboard_widget.save_file(self.whiteboard_widget.active_file_path)
             return

        # 2. Fallback to current folder default if visible
        if self.current_folder and self.whiteboard_widget.isVisible():
            folder_path = self.data_manager.get_folder_path(self.current_folder)
            if folder_path:
                wb_path = os.path.join(folder_path, "whiteboard.json")
                self.whiteboard_widget.save_file(wb_path)
                
    def insert_image_to_note(self, image_path, metadata=None):
        """Insert whiteboard snapshot into current note.
           If we are in 'editing mode' for a specific image, replace it.
           Otherwise, insert as new.
        """
        if not self.current_note:
            self.show_message(QMessageBox.Icon.Warning, "No Note", "Please open a note to insert the drawing.")
            return

        # Check for replacement mode
        if self.editing_image_id:
            # We are editing an existing image -> Replace it
            res_name = self.editing_image_id
            success = self.editor.replace_image_resource(res_name, image_path, metadata)
            
            if success:
                self.show_message(QMessageBox.Icon.Information, "Updated", "Drawing updated successfully.")
            else:
                # Fallback if replacement failed (e.g. image deleted while editing)
                self.editor.insert_image_from_path(image_path, metadata)
                self.show_message(QMessageBox.Icon.Information, "Inserted", "Original missing, inserted as new.")
            
            # Clear editing state
            self.editing_image_id = None
        else:
            # Standard Insertion
            self.editor.insert_image_from_path(image_path, metadata)
            self.show_message(QMessageBox.Icon.Information, "Inserted", "Drawing inserted into note.")

    def jump_to_whiteboard(self, metadata):
        """Open whiteboard and jump to specific page"""
        if not self.whiteboard_widget.isVisible():
            self.whiteboard_widget.setVisible(True)
            
        # 1. Collapse Sidebars (User Request: "open complete")
        # Access main splitter (Sidebar, NoteList, Content)
        main_splitter = self.centralWidget()
        if isinstance(main_splitter, QSplitter):
            total_w = main_splitter.width()
            # Collapse Sidebar (0) and NoteList (1), give all to Content (2)
            main_splitter.setSizes([0, 0, total_w])

        # 2. Ensure 50/50 split layout between Whiteboard and Editor
        # ContentSplitter: Highlight (0), Whiteboard (1), Editor (2)
        sizes = self.content_splitter.sizes()
        h_view_size = sizes[0] # Preserve highlight view
        
        # Use large equal numbers to enforce 50/50 ratio
        self.content_splitter.setSizes([h_view_size, 10000, 10000])
        
        # Load specific whiteboard file if provided (Cross-folder support)
        if 'wb_file' in metadata and metadata['wb_file']:
             import os
             if os.path.exists(metadata['wb_file']):
                 # Check if we need to switch file
                 if self.whiteboard_widget.active_file_path != metadata['wb_file']:
                     self.whiteboard_widget.load_file(metadata['wb_file'])
            
        if 'wb_page' in metadata:
             self.whiteboard_widget.go_to_page(metadata['wb_page'])
             
        # Track which image we are editing (if provided)
        if '_res_name' in metadata:
            self.editing_image_id = metadata['_res_name']
        else:
            self.editing_image_id = None

    def _extract_highlights(self, notes):
        """Helper to extract highlights from notes using Logical IDs."""
        from bs4 import BeautifulSoup, NavigableString
        import re
        from PyQt6.QtGui import QColor
        import uuid

        grouped_highlights = {}
        total_count = 0
        
        # Get custom color from settings
        custom_hl_color = self.data_manager.get_setting("custom_highlight_color", "cyan")
        
        # Normalize colors to hex for comparison
        def normalize_color(c):
             try:
                 col = QColor(c)
                 if col.isValid():
                     return col.name().lower() # Returns #rrggbb
             except:
                 pass
             return str(c).lower()

        # Define Known Colors (Hex) - Normalized to lowercase
        valid_colors = {
            "#ffff00", "yellow", # Standard Yellow
            "#00ffff", "cyan",   # Standard Cyan
            "#00ff00", "lime",   # Green
            "#ff00ff", "magenta",# Pink/Magenta
            "#ff0000", "red",    # Red
            "#ffa500", "orange", # Orange
            "#b0b000",           # Dark Mode Gold
            normalize_color(custom_hl_color) # USER CUSTOM COLOR
        }
        
        # Check setting
        only_custom = self.data_manager.get_setting("strict_highlight_export", True)

        def is_valid_bg(c_hex):
            if not c_hex: return None
            c_hex = c_hex.lower()
            norm_hex = c_hex
            try:
                col = QColor(c_hex)
                if col.isValid():
                     norm_hex = col.name().lower()
            except: pass
            
            if not only_custom: return norm_hex
            if norm_hex in valid_colors: return norm_hex
            if c_hex in valid_colors: return norm_hex
            return None

        for note in notes:
            # SAFETY: Skip notes with no content or invalid states
            if not note:
                continue
            if not hasattr(note, 'content'):
                continue
            if note.content is None:
                continue
            if not isinstance(note.content, str):
                continue
            if len(note.content.strip()) == 0:
                continue
            
            try:
                soup = BeautifulSoup(note.content, 'html.parser')
                
                # Capture all potential highlight tags
                # We specifically look for tags with title starting with hl_ OR existing style-based selection
                candidate_tags = soup.select('[style*="background"], u, [style*="text-decoration"], [title^="hl_"]')
                # print(f"DEBUG: Candidate Tags Found: {len(candidate_tags)}")
                
                processed_tags = set()
                items = []
                
                # Temporary storage for grouping
                # Map: GroupID -> List of items
                # We need to maintain ORDER
                ordered_groups = [] # List of {'id': id, 'items': [item1, item2], 'color': c, 'type': t}
                
                # Legacy Continuity Helper
                last_legacy_group = None
                
                for tag in candidate_tags:
                    if tag in processed_tags: continue
                    
                    # 1. Extract Info
                    style = tag.get("style", "").lower()
                    title = tag.get("title", "")
                    
                    # Logic Type
                    hid = None
                    
                    # EXTRACT ID FROM FONT FAMILY (Robust Persistence)
                    # Look for hl_ or ul_ in the style string
                    id_match = re.search(r"(?:'|\"| |^)(hl_[a-f0-9]{8,}|ul_[a-f0-9]{8,})(?:'|\"|;|$)", style)
                    if id_match:
                         hid = id_match.group(1)

                    # Formatting Check (Moved UP to allow fallback)
                    bg_color = None
                    final_type = None
                    
                    # Background check
                    # Background check
                    if "background" in style:
                        m = re.search(r'background(?:-color)?:\s*([^;"]+)', style)
                        if m:
                            c = m.group(1).strip()
                            norm_bg = is_valid_bg(c)
                            if norm_bg:
                                bg_color = norm_bg
                                final_type = 'highlight'
                            elif hid and hid.startswith('hl_'):
                                # PERSISTENCE FALLBACK:
                                # If strict check failed (color not in whitelist) BUT we have a valid Logical ID,
                                # we explicitly TRUST this is a highlight and safeguard the color used.
                                bg_color = normalize_color(c)
                                final_type = 'highlight'
                    
                    # Underline check
                    if not final_type:
                        is_u = False
                        if tag.name == 'u': is_u = True
                        if "text-decoration" in style and "underline" in style: is_u = True
                        
                        # Strict Ignore
                        if tag.name == 'a' or tag.find_parent('a'): is_u = False
                        if tag.name in ['pre', 'code', 'textarea']: is_u = False
                        
                        if is_u:
                            final_type = 'underline'

                    # STRICT MODE CHECK
                    # We accept the tag if:
                    # 1. It has a Logical ID (Strongest)
                    # 2. It has a Valid Highlight Color (Fallback for Code blocks where Font is stripped)
                    
                    is_valid_highlight = False
                    if hid:
                        is_valid_highlight = True
                    elif final_type == 'highlight' and bg_color:
                        # Validated by is_valid_bg whitelist
                        is_valid_highlight = True
                    elif final_type == 'underline' and hid:
                        # For underlines, we still prefer strict ID? 
                        # Or should we allow any non-link underline? 
                        # Let's trust ID for underlines for now to assume 'Ctrl+U'
                        is_valid_highlight = True
                        
                    if not is_valid_highlight:
                        continue

                    if not final_type and hid:
                         # If we have an ID but no type detected (e.g. style separation), 
                         # try to infer type from ID prefix
                         if hid.startswith('hl_'): final_type = 'highlight'
                         elif hid.startswith('ul_'): final_type = 'underline'

                    if not final_type: continue

                    # Extract Text
                    raw_html = tag.decode_contents()
                    # Strip styles for clean preview
                    raw_html = re.sub(r'\s*style="[^"]*"', '', raw_html)
                    raw_html = re.sub(r"\s*style='[^']*'", '', raw_html)
                    raw_html = re.sub(r'\s*class="[^"]*"', '', raw_html)
                    text = raw_html.strip()
                    
                    if not text: continue
                    
                    # Calculate Indent
                    indent = 0
                    curr = tag
                    while curr and hasattr(curr, 'name') and curr.name not in ['body', '[document]']:
                         if curr.name in ['ul', 'ol', 'blockquote']: indent += 20
                         if hasattr(curr, 'get'):
                             s = curr.get('style', '').lower()
                             if 'margin-left' in s:
                                 m = re.search(r'margin-left:\s*(\d+)px', s)
                                 if m: indent += int(m.group(1))
                         curr = curr.parent

                    item_data = {
                        'text': text,
                        'tag': tag,
                        'indent': indent
                    }
                    
                    # GROUPING LOGIC
                    target_group = None
                    
                    # A. Logic ID Grouping (Strong)
                    if hid:
                        # Search existing groups for this ID
                        for group in ordered_groups:
                            if group['id'] == hid:
                                target_group = group
                                break
                        
                        if not target_group:
                            # Create new group
                            target_group = {
                                'id': hid,
                                'type': final_type,
                                'color': bg_color,
                                'items': []
                            }
                            ordered_groups.append(target_group)
                            
                        # Add to group
                        target_group['items'].append(item_data)
                        last_legacy_group = None # Break legacy chain
                        
                    # B. Legacy/Fallback Grouping (Weak - Spatial)
                    else:
                        # Try to merge with previous if:
                        # 1. No HID involved
                        # 2. Same Color & Type
                        # 3. Continuity (Spatial)
                        
                        merged = False
                        if last_legacy_group:
                            if last_legacy_group['id'] is None: # Only merge with other legacy items
                                if last_legacy_group['type'] == final_type and last_legacy_group['color'] == bg_color:
                                    # Simple Continuity: Is this tag close to the last one?
                                    # We can use the simple heuristic: Are they in same block?
                                    # Or just strict adjacency.
                                    # Let's assume adjacency if sequential in list.
                                    # (Since we iterate document order)
                                    target_group = last_legacy_group
                                    target_group['items'].append(item_data)
                                    merged = True
                        
                        if not merged:
                            # New Legacy Group
                            target_group = {
                                'id': None,
                                'type': final_type,
                                'color': bg_color,
                                'items': [item_data]
                            }
                            ordered_groups.append(target_group)
                        
                        last_legacy_group = target_group

                    processed_tags.add(tag)

                # Finalize Groups to Items
                for group in ordered_groups:
                    # Combine Texts
                    full_text = ""
                    for i, itm in enumerate(group['items']):
                        t = itm['text']
                        if i > 0:
                            # Smart Separator Logic
                            prev_itm = group['items'][i-1]
                            # Check if they share the same parent (Inline flow)
                            # If parents differ, it likely means a block break (e.g. <li> vs <li>)
                            if itm['tag'].parent == prev_itm['tag'].parent:
                                full_text += " " + t
                            else:
                                full_text += "\n" + t
                        else:
                            full_text = t
                            
                    items.append({
                        'text': full_text,
                        'color': group['color'],
                        'type': group['type'],
                        'indent': group['items'][0]['indent'] # Use first indent
                    })

                if items:
                    grouped_highlights[note.id] = {'title': note.title, 'items': items}
                    total_count += len(items)

            except Exception as e:
                print(f"Error parsing note {note.id}: {e}")
                import traceback
                traceback.print_exc()
            except Exception as e:
                print(f"ERROR processing note {note.id}: {e}")
                import traceback
                traceback.print_exc()
                continue
        return grouped_highlights, total_count

    def handle_highlight_link(self, url):
        """Handle execution of links from highlight view"""
        scheme = url.scheme()
        if scheme == "cmd":
            # Handle cmd://command (host) or cmd:///command (path)
            command = url.host() if url.host() else url.path().strip('/')
            
            if command == "close":
                self.show_highlight_preview()
            elif command == "export_pdf":
                self.export_current_highlights()
            elif command == "toggle_numbering":
                self.highlight_numbering_continuous = not self.highlight_numbering_continuous
                self.refresh_highlight_preview_if_visible()
        elif scheme == "note":
            note_id = url.path()
            self._open_note_and_scroll(note_id)
        elif scheme == "jump":
            # format: jump://note_id/text_snippet
            # Robust URL parsing using QUrl methods
            note_id = url.host()
            path = url.path()
            
            # path includes leading slash, remove it
            if path.startswith('/'):
                path = path[1:]
                
            if note_id and path:
                from urllib.parse import unquote
                text = unquote(path)
                self._open_note_and_scroll(note_id, text)

    def refresh_highlight_preview_if_visible(self):
        """Refreshes the highlight preview if it is currently visible, maintaining scroll."""
        try:
            if hasattr(self, 'highlight_view') and self.highlight_view.isVisible():
                # SAFETY: Ensure we have a valid folder with notes
                if not self.current_folder:
                    print("DEBUG: refresh_highlight_preview_if_visible - no current folder")
                    return
                if not hasattr(self.current_folder, 'notes'):
                    print("DEBUG: refresh_highlight_preview_if_visible - folder has no notes attribute")
                    return
                if not self.current_folder.notes:
                    print("DEBUG: refresh_highlight_preview_if_visible - folder.notes is empty")
                    # Empty is OK, just show empty preview
                    grouped_highlights, total_count = {}, 0
                    html_content = self._generate_highlight_preview_html(grouped_highlights, total_count)
                    self.highlight_view.setHtml(html_content)
                    return
                
                # Save Scroll Position
                v_scroll_bar = self.highlight_view.verticalScrollBar()
                v_pos = v_scroll_bar.value()
                
                # Re-extract
                try:
                     sorted_notes = sorted(self.current_folder.notes, key=lambda n: n.order)
                except:
                     sorted_notes = self.current_folder.notes
                     
                grouped_highlights, total_count = self._extract_highlights(sorted_notes)
                
                # Generate HTML
                html_content = self._generate_highlight_preview_html(grouped_highlights, total_count)
                self.highlight_view.setHtml(html_content)
                
                # Restore Scroll
                v_scroll_bar.setValue(v_pos)
        except Exception as e:
            print(f"CRASH PREVENTION: Error in refresh_highlight_preview_if_visible: {e}")
            import traceback
            traceback.print_exc()

    def _open_note_and_scroll(self, note_id, text_to_find=None):
        # Select Note
        if not self.current_note or self.current_note.id != note_id:
             self.note_list.select_note_by_id(note_id)
        
        # Scroll to text if provided
        if text_to_find:
            # Move cursor to start
            cursor = self.editor.editor.textCursor()
            cursor.setPosition(0)
            self.editor.editor.setTextCursor(cursor)
            
            # Find Strategy (Robust)
            # 1. Exact Match
            found = self.editor.editor.find(text_to_find)
            
            # 2. Normalized Match (Try replacing newlines with spaces)
            if not found and "\n" in text_to_find:
                self.editor.editor.moveCursor(QTextCursor.MoveOperation.Start) # Reset
                normalized = text_to_find.replace("\n", " ")
                found = self.editor.editor.find(normalized)
                
            # 3. Prefix Match (First line/segment)
            if not found:
                 self.editor.editor.moveCursor(QTextCursor.MoveOperation.Start) # Reset
                 # Try first line or first 60 chars
                 prefix = text_to_find.split('\n')[0]
                 if len(prefix) > 60: prefix = prefix[:60]
                 found = self.editor.editor.find(prefix)
            
            if found:
                self.editor.editor.ensureCursorVisible()
                # Flash selection logic could be added here if needed

    def _generate_highlight_preview_html(self, grouped_highlights, total_count, override_theme=None, for_export=False):
        """Generate HTML (Links instead of badges)"""
        from PyQt6.QtGui import QColor
        if override_theme:
            is_dark = (override_theme == "dark")
        else:
            is_dark = self.data_manager.get_setting("theme_mode", "light") == "dark"
        bg = "#1e1e1e" if is_dark else "#ffffff"
        text = "#e0e0e0" if is_dark else "#333333"
        item_bg = "#2d2d2d" if is_dark else "#f9f9f9"
        border = "#444" if is_dark else "#ddd"
        link = "#4da6ff" if is_dark else "#0066cc"
        
        html = f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><style>
        body{{font-family:'Segoe UI';padding:20px;background-color:{bg};color:{text};}}
        
        .btn {{
        text-decoration: none;
        padding: 8px 16px;
        border-radius: 4px;
        font-size: 0.9em; 
        font-weight: bold;
        color: white;
        display: inline-block;
    }}
    .btn-primary {{ background-color: #007ACC; border: 1px solid #005a9e; }}
    .btn-secondary {{ background-color: #666666; border: 1px solid #444444; }}

    h3{{margin-top:0;color:{text};}}
    .toc{{background:{item_bg};padding:15px;border-radius:5px;margin-bottom:25px;border:1px solid {border};}}
    .toc-title{{font-weight:bold;margin-bottom:10px;display:block;}}
    .toc ul{{list-style-type:none;padding-left:10px;margin:0;}}
    .toc li{{margin-bottom:5px;}}
    .toc a{{text-decoration:none;color:{link};}}
    .toc a:hover{{text-decoration:underline;}}

    .note-section{{margin-bottom:30px;}}
    .note-title{{font-size:1.1em;margin-bottom:10px;border-bottom:1px solid {border};color:{link};padding-bottom:5px;}}
    .item{{background:{item_bg};padding:6px;margin:6px 0;border-left:3px solid {border};display:flex;align-items:center;min-height:24px;}}
    .hl-text{{color:black;padding:1px 3px;border-radius:2px;margin-right:8px;flex:1;font-size:0.9em;line-height:1.4;white-space:pre-wrap;}}
    .ul-text{{text-decoration:underline;color:{text};margin-right:8px;flex:1;font-size:0.9em;line-height:1.4;white-space:pre-wrap;}}
    .link-icon{{text-decoration:none;font-size:1.2em;cursor:pointer;}}
    
    /* FIX: Normalize headers inside highlights so they don't blow up the UI */
    .hl-text h1, .hl-text h2, .hl-text h3, .hl-text h4, .hl-text h5, .hl-text h6 {{
        font-size: 1.1em; 
        margin: 0; 
        display: inline; 
        font-weight: bold;
    }}
    .hl-text p {{ margin: 0; display: inline; }}
    </style></head><body>
    
    <table width="100%" border="0" cellpadding="0" cellspacing="0" style="margin-bottom:20px; border-bottom:2px solid {link}; padding-bottom:10px;">
    <tr>
        <td width="100%" valign="middle">
            <div style="font-size:1.4em;font-weight:bold;color:{link};">{self.current_folder.name}</div>
        </td>
        <td valign="middle" style="white-space:nowrap;">'''
            
        # Hide Buttons for PDF Export
        if not for_export:
            html += f'''
                <!-- Buttons Table -->
                <table border="0" cellpadding="0" cellspacing="0">
                    <tr>
                        <td bgcolor="#007ACC" style="padding: 6px 12px; border-radius: 4px; border: 1px solid #005a9e;">
                            <a href="cmd://export_pdf" style="text-decoration: none; color: white; font-weight: bold; font-size: 0.9em; display: block;">Export PDF 📥</a>
                        </td>
                        <td width="10"></td> <!-- Spacer -->
                        <td bgcolor="#666666" style="padding: 6px 12px; border-radius: 4px; border: 1px solid #444444;">
                            <a href="cmd://close" style="text-decoration: none; color: white; font-weight: bold; font-size: 0.9em; display: block;">Close ✕</a>
                        </td>
                    </tr>
                </table>'''
                
        html += '''
            </td>
        </tr>
        </table>'''
    
        # Toggle Label Logic (Hide for export)
        toggle_link = ""
        if not for_export:
            if self.highlight_numbering_continuous:
                toggle_text = "🔢 Switching to: Restart Per Note"
                mode_display = "(Continuous)"
            else:
                toggle_text = "🔢 Switching to: Continuous Numbering"
                mode_display = "(Restart Per Note)"
                
            toggle_link = f'<span style="font-size:0.7em; margin-left:15px; font-weight:normal;">Mode: {mode_display} <a href="cmd://toggle_numbering" style="color:{link};text-decoration:none;margin-left:5px;">[{toggle_text}]</a></span>'
        
        html += f'''<h3>Highlights ({total_count}){toggle_link}</h3>
        
        <div class="toc">
            <span class="toc-title">Table of Contents</span>
            <ul>'''
            
        from urllib.parse import quote
        
        # TOC Generator
        for note_id, group in grouped_highlights.items():
             html += f'<li><a href="note://{note_id}">{group["title"]}</a> <span style="color:#888;font-size:0.9em;">({len(group["items"])})</span></li>'
        html += '</ul></div>'
        
        # Content Generator
        global_idx = 1
        for note_id, group in grouped_highlights.items():
            html += f'<div class="note-section"><div class="note-title">{group["title"]}</div>'
            for i, item in enumerate(group['items'], 1):
                
                # Numbering Logic
                if self.highlight_numbering_continuous:
                    display_idx = global_idx
                    global_idx += 1
                else:
                    display_idx = i
                # Safely escape text for URL but NOT for display (we want standard display)
                # But HTML entities need handling? Browsers handle plain utf-8 fine usually.
                safe_text = quote(item['text']) 
                
                # Apply Indentation
                indent = item.get('indent', 0)
                # Cap indentation to prevent UI breaking (e.g. max 200px)
                indent = min(indent, 200)
                # FIX: Apply indent to Content Cell padding, not Table margin
                # This ensures Numbers (1., 2., 3.) remain left-aligned vertically.
                content_indent_style = f"padding-left: {indent}px;" if indent > 0 else ""
                
                # Dynamic Background
                bg_style = ""
                fg_style = ""
                
                if item['color']:
                    bg_style = f"background-color:{item['color']};"
                    try:
                        fg_style = "color:white;" if QColor(item['color']).lightness() < 128 else "color:black;"
                    except:
                        fg_style = "color:black;"
                
                # Numbering Style
                # i is already 1-based index
                
                # Table Layout for robust side-by-side (QTextBrowser doesn't support Flexbox)
                # Structure: [Number Cell] [Content Cell] [Link Cell]
                
                link_html = f'<a href="jump://{note_id}/{safe_text}" class="link-icon" title="Jump to context" style="text-decoration:none;">🔗</a>'
                
                if for_export:
                    link_html = "" # No links in PDF export
                
                # Determine Content Style
                # Added border-radius for aesthetics
                content_style = f"{bg_style}{fg_style}display:inline-block;"
                if item['type'] == 'underline':
                    content_style = f"text-decoration:underline;color:{text};"
                    
                # We use a nested table for the item to handle Indentation + Layout
                # Indent is REMOVED from table margin and applied to content cell
                
                html += f'''
                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom:6px;">
                    <tr>
                        <td width="24" valign="top" style="vertical-align:top;padding-top:4px;">
                            <span style="color:{text};font-weight:bold;font-size:0.9em;">{display_idx}.</span>
                        </td>
                        <td valign="top" style="vertical-align:top;{content_indent_style}">
                            <div class="hl-text" style="{content_style}">{item['text']}</div>
                        </td>
                        <td width="30" valign="top" align="right" style="vertical-align:top;text-align:right;">
                            {link_html}
                        </td>
                    </tr>
                </table>
                '''
            html += '</div>'
            
        html += '</body></html>'
        return html


    def _export_highlights_pdf(self, grouped_highlights, total_count):
        """Export highlights to PDF"""
        from PyQt6.QtWidgets import QFileDialog
        import os
        
        default_name = f"{self.current_folder.name}_highlights.pdf"
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Highlights to PDF",
            os.path.join(os.path.expanduser("~"), default_name),
            "PDF Files (*.pdf)"
        )
        
        if not file_path:
            return
        
        # Use simple logic first
        try:
            html_content = self._generate_highlight_preview_html(grouped_highlights, total_count)
            from pdf_export.exporter import export_html_to_pdf
            
            # Theme Selection Dialog
            current_theme = self.data_manager.get_setting("theme_mode", "light")
            
            from ui.theme_dialog import ThemeExportDialog
            dialog = ThemeExportDialog(self, current_theme)
            
            if not dialog.exec():
                return
                
            theme_mode = dialog.get_selected_theme()
            selected_theme_str = "dark" if theme_mode == 1 else "light" # For HTML gen override
            
            # Regenerate HTML with correct theme colors
            html_content = self._generate_highlight_preview_html(
                grouped_highlights, total_count, 
                override_theme=selected_theme_str,
                for_export=True
            )
            
            export_html_to_pdf(html_content, file_path, self.current_folder.name + " - Highlights", theme=theme_mode)
            self.show_message(QMessageBox.Icon.Information, "Export Complete", 
                             f"Highlights exported successfully to:\n{file_path}")
        except Exception as e:
            self.show_message(QMessageBox.Icon.Critical, "Export Failed", 
                             f"Failed to export highlights:\n{e}")
    
    def show_message(self, icon, title, text, details=None):
        """Helper to show messages that stay on top of the whiteboard."""
        msg = QMessageBox(self)
        msg.setIcon(icon)
        msg.setWindowTitle(title)
        msg.setText(text)
        if details:
            msg.setDetailedText(details)
        msg.setWindowFlags(msg.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        return msg.exec()
    def refresh_metadata(self):
        """Update the metadata bar with current editor stats."""
        if not self.current_note:
            return
            
        text = self.editor.editor.toPlainText()
        
        # Format modified time
        modified_time = "--"
        from datetime import datetime
        
        raw_ts = getattr(self.current_note, 'modified_at', None) or getattr(self.current_note, 'created_at', None)
        
        if raw_ts:
            try:
                if isinstance(raw_ts, str):
                    # Handle ISO format strings
                    dt = datetime.fromisoformat(raw_ts)
                else:
                    # Handle numeric timestamps
                    dt = datetime.fromtimestamp(raw_ts)
                modified_time = dt.strftime("%Y-%m-%d %I:%M:%S %p")
            except Exception as e:
                logger.error(f"Error parsing timestamp {raw_ts}: {e}")
             
        self.metadata_bar.update_stats(text, modified_time)

    def on_view_mode_changed(self, mode):
        """Persist view mode preference for current folder."""
        if self.current_folder and self.current_folder.id not in ["RECENT_ROOT", "TRASH_ROOT", "ARCHIVED_ROOT", "ALL_NOTEBOOKS_ROOT"]:
            self.current_folder.view_mode = mode
            # We update the folder metadata via Sidebar signal or DataManager directly?
            # DataManager doesn't have granular update for arbitrary fields easily Exposed.
            # But the Sidebar handles 'updateFolder' signal which calls MainWindow.update_folder.
            # MainWindow.update_folder updates 'folders_meta'.
            # Let's reuse that pipeline.
            self.sidebar.updateFolder.emit(self.current_folder.id, {"view_mode": mode})


