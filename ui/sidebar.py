from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, 
    QLineEdit, QPushButton, QHBoxLayout, QMenu, QMessageBox, QFileDialog,
    QFrame, QLabel, QComboBox, QSizePolicy, QColorDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QRect
from PyQt6.QtGui import QFont, QColor, QAction, QPainter, QIcon
from ui.color_delegate import ColorDelegate, COLOR_ROLE
from util.icon_factory import get_premium_icon, get_combined_indicators
from ui.zen_dialog import ZenInputDialog

class Sidebar(QWidget):
    folderSelected = pyqtSignal(str) # Emits folder ID
    createFolder = pyqtSignal(str, str) # folder_name, notebook_id
    deleteFolder = pyqtSignal(str)   # Emits folder ID
    renameFolder = pyqtSignal(str, str)  # Emits folder ID, new name
    exportFolder = pyqtSignal(str)   # Emits folder ID for export
    exportWhiteboard = pyqtSignal(str) # Emits folder ID for whiteboard export
    updateFolder = pyqtSignal(str, dict) # Emits folder ID, updates dict
    reorderFolder = pyqtSignal(str, int) # Emits folder ID, new position (index)
    requestHighlightPreview = pyqtSignal(str) # folder_id
    requestPdfPreview = pyqtSignal(str) # folder_id
    toggleTheme = pyqtSignal()
    wrapToggled = pyqtSignal(bool)
    createNotebook = pyqtSignal(str)
    deleteNotebook = pyqtSignal(str)
    lockToggled = pyqtSignal(bool)
    panelToggleRequest = pyqtSignal() # Phase 46

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        self.all_folders = []
        self.all_notebooks = []
        self.sort_descending = True
        self.showing_archived = False
        self.theme_mode = "light" # Track current theme

        self._setup_header()
        self._setup_search()
        self._setup_list()
        self._setup_bottom()

    def _setup_header(self):
        header_container = QWidget()
        header_container.setObjectName("SidebarHeader") # For Global Styling
        header_layout = QVBoxLayout(header_container)
        header_layout.setContentsMargins(16, 20, 16, 16) # More breathing room
        header_layout.setSpacing(16)
        
        # --- ROW 1: BRANDING ---
        brand_row = QWidget()
        brand_layout = QHBoxLayout(brand_row)
        brand_layout.setContentsMargins(0, 0, 0, 0)
        brand_layout.setSpacing(10)
        
        # Logo Container
        self.logo_container = QFrame()
        self.logo_container.setObjectName("SidebarLogoContainer")
        self.logo_container.setFixedSize(36, 36)
        container_layout = QHBoxLayout(self.logo_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.logo_label = QLabel()
        self.logo_label.setPixmap(QIcon("logo_transparent.png").pixmap(24, 24))
        self.logo_label.setFixedSize(24, 24)
        self.logo_label.setScaledContents(True)
        container_layout.addWidget(self.logo_label)
        
        brand_layout.addWidget(self.logo_container)
        
        # Title
        self.title_label = QLabel("Zen Notes")
        self.title_label.setObjectName("SidebarTitle")
        brand_layout.addWidget(self.title_label)
        
        brand_layout.addStretch()
        
        # Theme Toggle (Top Right)
        self.theme_btn = QPushButton() 
        self.theme_btn.setToolTip("Toggle Zen Mode")
        self.theme_btn.setFixedSize(32, 32)
        self.theme_btn.setIconSize(QSize(20, 20))
        self.theme_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_btn.clicked.connect(self.toggleTheme.emit)
        brand_layout.addWidget(self.theme_btn)

        # Panel Toggle (Phase 46)
        self.panel_btn = QPushButton()
        self.panel_btn.setToolTip("Toggle Note Panel")
        self.panel_btn.setFixedSize(32, 32)
        self.panel_btn.setIconSize(QSize(20, 20))
        self.panel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.panel_btn.clicked.connect(self.panelToggleRequest.emit)
        brand_layout.addWidget(self.panel_btn)
        
        header_layout.addWidget(brand_row)
        
        # --- ROW 2: NOTEBOOK SELECTOR ---
        nb_row = QWidget()
        nb_layout = QHBoxLayout(nb_row)
        nb_layout.setContentsMargins(0,0,0,0)
        
        self.nb_selector = QComboBox()
        self.nb_selector.setObjectName("SidebarNotebookSelector") # Global styling
        self.nb_selector.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.nb_selector.setCursor(Qt.CursorShape.PointingHandCursor)
        self.nb_selector.currentIndexChanged.connect(self.on_notebook_changed)
        
        # Improve popup
        view = self.nb_selector.view()
        view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        view.setWordWrap(True)
        view.setMinimumWidth(300)
        
        nb_layout.addWidget(self.nb_selector)
        header_layout.addWidget(nb_row)

        # --- ROW 3: ACTIONS & UTILITIES ---
        action_row = QWidget()
        action_layout = QHBoxLayout(action_row)
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.setSpacing(4) # Tight spacing for toolbars
        
        # Group 1: Notebook Management
        self.add_folder_btn = QPushButton()
        self.add_folder_btn.setIcon(get_premium_icon("plus"))
        self.add_folder_btn.setFixedSize(32, 32)
        self.add_folder_btn.setToolTip("New Notebook")
        self.add_folder_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_folder_btn.clicked.connect(self.prompt_new_notebook)
        action_layout.addWidget(self.add_folder_btn)

        self.delete_nb_btn = QPushButton()
        self.delete_nb_btn.setIcon(get_premium_icon("trash")) 
        self.delete_nb_btn.setFixedSize(32, 32)
        self.delete_nb_btn.setToolTip("Delete Notebook")
        self.delete_nb_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.delete_nb_btn.clicked.connect(self._on_delete_notebook_clicked)
        action_layout.addWidget(self.delete_nb_btn)
        
        action_layout.addSpacing(8)
        
        # Group 2: View Options
        self.sort_btn = QPushButton()
        self.sort_btn.setIcon(get_premium_icon("sort_down"))
        self.sort_btn.setToolTip("Sort by Date")
        self.sort_btn.setFixedSize(32, 32)
        self.sort_btn.setCheckable(True)
        self.sort_btn.setChecked(True)
        self.sort_btn.clicked.connect(self.toggle_sort)
        action_layout.addWidget(self.sort_btn)
        
        self.wrap_btn = QPushButton()
        self.wrap_btn.setIcon(get_premium_icon("wrap"))
        self.wrap_btn.setToolTip("Toggle Wrap")
        self.wrap_btn.setFixedSize(32, 32)
        self.wrap_btn.setCheckable(True)
        self.wrap_btn.clicked.connect(lambda: self.wrapToggled.emit(self.wrap_btn.isChecked()))
        action_layout.addWidget(self.wrap_btn)
        
        self.preview_btn = QPushButton()
        self.preview_btn.setIcon(get_premium_icon("eye"))
        self.preview_btn.setToolTip("Preview PDF")
        self.preview_btn.setFixedSize(32, 32)
        self.preview_btn.clicked.connect(self.requestPdfPreview.emit)
        action_layout.addWidget(self.preview_btn)

        action_layout.addStretch()

        # Lock (Aligned Right)
        self.lock_btn = QPushButton()
        self.lock_btn.setIcon(get_premium_icon("unlock"))
        self.lock_btn.setToolTip("Lock Navigation")
        self.lock_btn.setCheckable(True)
        self.lock_btn.setFixedSize(32, 32)
        self.lock_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lock_btn.toggled.connect(self._on_lock_toggled)
        action_layout.addWidget(self.lock_btn)
        
        # Removed highlight_preview_btn to de-clutter (can access via menu or standard shortcuts?)
        # Or keep it if critical. The user didn't explicitly ask for it in the redesign.
        # I'll enable it if space permits, but for now focus on clean UI.
        self.highlight_preview_btn = QPushButton()
        self.highlight_preview_btn.setIcon(get_premium_icon("bookmark"))
        self.highlight_preview_btn.setToolTip("Highlights")
        self.highlight_preview_btn.setFixedSize(32, 32)
        self.highlight_preview_btn.clicked.connect(self.requestHighlightPreview.emit)
        action_layout.insertWidget(action_layout.count() - 1, self.highlight_preview_btn) # Insert before lock

        header_layout.addWidget(action_row)
        self.layout.addWidget(header_container)

    def _setup_search(self):
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search folders...")
        self.search_bar.textChanged.connect(self.refresh_list)
        self.layout.addWidget(self.search_bar)

    def _setup_list(self):
        self.list_widget = QTreeWidget()
        self.list_widget.setObjectName("FolderTree")
        self.list_widget.setHeaderHidden(True)
        self.list_widget.setIndentation(15)
        self.list_widget.setAnimated(True)
        self.list_widget.setRootIsDecorated(True)
        self.list_widget.setUniformRowHeights(True)
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        self.list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)
        self.layout.addWidget(self.list_widget)

    def load_notebooks(self, notebooks):
        self.all_notebooks = notebooks
        self.update_notebook_selector()
        
    def update_notebook_selector(self):
        """Rebuild the selector dropdown and restore current selection."""
        # Store current selection data to restore it later
        current_data = self.nb_selector.currentData()
        
        self.nb_selector.blockSignals(True)
        self.nb_selector.clear()
        
        for i, nb in enumerate(self.all_notebooks, 1):
            # Use icon-like prefixes for a premium look
            self.nb_selector.addItem(f"📁 {i}. {nb.name}", nb.id)
            
        # Try to restore previous selection
        idx = self.nb_selector.findData(current_data)
        if idx >= 0:
            self.nb_selector.setCurrentIndex(idx)
        else:
            self.nb_selector.setCurrentIndex(0) # Default to ALL
            
        self.nb_selector.blockSignals(False)

    def on_notebook_changed(self, index):
        self.refresh_list()

    def _on_lock_toggled(self, locked):
        self.lock_btn.setIcon(get_premium_icon("lock" if locked else "unlock", color="white"))
        self.lockToggled.emit(locked)

    def set_theme_mode(self, mode):
        """Updates the sidebar header and components for the given theme mode."""
        is_dark = mode == "dark"
        icon_color = "#FFFFFF" if is_dark else "#09090b" # Shadcn foreground
        
        # 1. Update Buttons Icons
        self.theme_mode = mode
        
        # Header Utility Icons
        self.theme_btn.setIcon(get_premium_icon("sun" if is_dark else "moon", color=icon_color))
        self.panel_btn.setIcon(get_premium_icon("panel_toggle", color=icon_color))
        
        # Action Bar Icons (if applicable)
        if hasattr(self, '_action_refresh'):
            self._action_refresh.setIcon(get_premium_icon("rotate_cw", color=icon_color))
        
        self.highlight_preview_btn.setIcon(get_premium_icon("bookmark", color=icon_color))
        self.preview_btn.setIcon(get_premium_icon("eye", color=icon_color))
        self.wrap_btn.setIcon(get_premium_icon("wrap", color=icon_color))
        
        # Sort icon
        sort_icon = "sort_up" if not self.sort_descending else "sort_down"
        self.sort_btn.setIcon(get_premium_icon(sort_icon, color=icon_color))
        
        # Action Icons
        # Note: Primary/Destructive buttons typically have contrasting text (white/white)
        self.add_folder_btn.setIcon(get_premium_icon("plus", color="white"))
        self.delete_nb_btn.setIcon(get_premium_icon("trash", color="white"))
        
        # Lock button (Normal: Icon Color, Checked: White)
        lock_color = "white" if self.lock_btn.isChecked() else icon_color
        self.lock_btn.setIcon(get_premium_icon("lock" if self.lock_btn.isChecked() else "unlock", color=lock_color))
        
        # 2. Refresh Tree Items (to update folder icons)
        self.refresh_list()

    def _on_delete_notebook_clicked(self):
        nb_id = self.nb_selector.currentData()
        if nb_id:
            self.confirm_delete_notebook(nb_id)

    def _setup_bottom(self):
        bottom_container = QWidget()
        bottom_layout = QVBoxLayout(bottom_container)
        bottom_layout.setContentsMargins(10, 10, 10, 10)

        self.add_btn = QPushButton(" New Folder")
        self.add_btn.setIcon(get_premium_icon("plus"))
        self.add_btn.setObjectName("NewFolderBtn")
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.clicked.connect(self.prompt_new_folder)
        bottom_layout.addWidget(self.add_btn)
        self.layout.addWidget(bottom_container)

    def set_wrap_mode(self, enabled):
        self.wrap_btn.setChecked(enabled)
        self.list_widget.setWordWrap(enabled)
        # Force a viewport update to trigger sizeHint recalculation
        self.list_widget.viewport().update()
        self.refresh_list()

    def toggle_sort(self):
        self.sort_descending = self.sort_btn.isChecked()
        self.sort_btn.setIcon(get_premium_icon("sort_down" if self.sort_descending else "sort_up"))
        self.sort_btn.setToolTip("Sort by Date (Newest First)" if self.sort_descending else "Sort by Date (Oldest First)")
        self.refresh_list()

    def load_folders(self, folders):
        self.all_folders = folders
        self.refresh_list()
        
    def refresh_list(self):
        search_text = self.search_bar.text().lower()
        # self.list_widget.clear() # Cleared at start of refresh

        # Preservation of expanded states could be done here, but strictly clearing for now.
        self.list_widget.clear()

        # --- DATA PREPARATION ---
        # 1. Get All Folders for current Notebook
        selected_nb_id = self.nb_selector.currentData()
        nb = next((n for n in self.all_notebooks if n.id == selected_nb_id), None)
        nb_folder_ids = nb.folder_ids if nb else []
        
        active_folders = []
        archived_folders = []
        
        # Special Folder: "Ideas & Sparks"
        ideas_folder = None
        
        for f in self.all_folders:
            # Check if this is the special "Ideas & Sparks" folder (by name for now)
            if f.name == "Ideas & Sparks" and f.id in nb_folder_ids:
                ideas_folder = f
                # Don't add to standard list if we want it ONLY in favorites
                # But user might want it in both? Let's put it in Favorites ONLY to avoid dupes.
                continue

            if f.id in nb_folder_ids:
                if getattr(f, 'is_archived', False):
                    archived_folders.append(f)
                else:
                    active_folders.append(f)
                    
        # Filter (Search)
        if search_text:
            active_folders = [f for f in active_folders if search_text in f.name.lower()]
            archived_folders = [f for f in archived_folders if search_text in f.name.lower()]
            if ideas_folder and search_text not in ideas_folder.name.lower():
                ideas_folder = None
        
        # Sort
        def sort_key(f):
            pinned_rank = not f.is_pinned
            prio = f.priority if f.priority > 0 else 999
            order_rank = getattr(f, 'order', 0)
            return (pinned_rank, prio, order_rank)
        
        active_folders.sort(key=sort_key)
        archived_folders.sort(key=sort_key)

        # --- UI BUILDING ---
        
        # 1. FAVORITES SECTION
        self._add_header_item("FAVORITES")
        
        # 1.1 Favorites (Pinned Folders)
        # Include Ideas & Sparks if found
        fav_folders = [f for f in active_folders if f.is_pinned]
        if ideas_folder:
            fav_folders.insert(0, ideas_folder)
            
        for f in fav_folders:
            item = self._create_folder_item(f)
            # Override icon for Favorites section to generic heart or keep folder?
            # Let's keep consistent folder icon but maybe force Heart icon if it's Ideas & Sparks
            if f.name == "Ideas & Sparks":
                 item.setIcon(0, get_premium_icon("heart", color="#F472B6"))
            
            self.list_widget.addTopLevelItem(item)

        # 1.2 Recent
        recent_item = QTreeWidgetItem(["Recent"])
        recent_item.setIcon(0, get_premium_icon("clock", color="#60A5FA")) # Blue clock
        recent_item.setData(0, Qt.ItemDataRole.UserRole, "RECENT_ROOT")
        self.list_widget.addTopLevelItem(recent_item)

        # Spacer
        self._add_spacer_item()

        # 2. FOLDERS SECTION
        self._add_header_item("FOLDERS")
        
        for i, folder in enumerate(active_folders, 1):
             f_item = self._create_folder_item(folder, index=i)
             self.list_widget.addTopLevelItem(f_item)
             
        # Spacer
        self._add_spacer_item()

        # 3. SYSTEM SECTION
        self._add_header_item("SYSTEM")
        
        # 3.1 Trash
        trash_item = QTreeWidgetItem(["Trash"])
        trash_item.setIcon(0, get_premium_icon("trash_2", color="#9CA3AF")) # Gray trash
        trash_item.setData(0, Qt.ItemDataRole.UserRole, "TRASH_ROOT")
        self.list_widget.addTopLevelItem(trash_item)
        
        # 3.2 Archived (Collapsible or just item)
        # Replicating old logic but under System
        if archived_folders:
             arch_item = QTreeWidgetItem([f"Archived ({len(archived_folders)})"])
             arch_item.setIcon(0, get_premium_icon("archive", color="#F59E0B")) # Amber archive
             arch_item.setData(0, Qt.ItemDataRole.UserRole, "ARCHIVED_ROOT")
             
             # Styling
             font = arch_item.font(0)
             # font.setBold(True)
             arch_item.setFont(0, font)

             self.list_widget.addTopLevelItem(arch_item)
             
             for i, folder in enumerate(archived_folders, 1):
                 f_item = self._create_folder_item(folder, index=i)
                 # Muted style for archived children?
                 f_item.setForeground(0, QColor("#A8A29E")) # Zinc 400
                 arch_item.addChild(f_item)
             
             if search_text:
                 arch_item.setExpanded(True)
             else:
                 arch_item.setExpanded(False)
        else:
             # Show empty Archived item?
             arch_item = QTreeWidgetItem(["Archived"])
             arch_item.setIcon(0, get_premium_icon("archive", color="#52525B")) # Darker
             arch_item.setData(0, Qt.ItemDataRole.UserRole, "ARCHIVED_ROOT")
             # Disable or show empty?
             # self.list_widget.addTopLevelItem(arch_item) 
             pass

    def _add_header_item(self, text):
        item = QTreeWidgetItem([text])
        item.setFlags(Qt.ItemFlag.NoItemFlags) # Non-selectable
        
        # Styling (Small Caps, Muted)
        font = item.font(0)
        font.setPointSize(9)
        font.setBold(True)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.0)
        item.setFont(0, font)
        
        # Color (handled by delegate or here)
        # Need to detect theme here or use a generic muted color
        is_dark = self.theme_mode == "dark"
        color = QColor("#52525B") if not is_dark else QColor("#A1A1AA") # Zinc 600 vs 400
        item.setForeground(0, color)
        # Add some padding visually? standard item doesn't support easy padding without delegate
        
        self.list_widget.addTopLevelItem(item)
    
    def _add_spacer_item(self):
        # A dummy item for spacing
        item = QTreeWidgetItem([""])
        item.setFlags(Qt.ItemFlag.NoItemFlags)
        # item.setSizeHint(0, QSize(0, 10)) # Requires SizeHint implementation in delegate or here
        # Quick hack: Empty item uses default height (~24px). 
        # Ideally we'd set a custom delegate to render separators. 
        # For now, just an empty non-selectable item acts as a spacer.
        self.list_widget.addTopLevelItem(item)

    def _create_folder_item(self, folder, index=None):
        prefix = ""
        if index is not None:
            prefix += f"{index}. "
            
        p = getattr(folder, 'priority', 0)
        if p == 1: prefix += "❶ "
        elif p == 2: prefix += "❷ "
        elif p == 3: prefix += "❸ "
        
        item = QTreeWidgetItem([f"{prefix}{folder.name}"])
        item.setData(0, Qt.ItemDataRole.UserRole, folder.id)
        if getattr(folder, 'color', None):
            item.setData(0, COLOR_ROLE, folder.color)
        
        # Combine Indicators
        indicators = ["folder"]
        if folder.is_pinned: indicators.append("pin")
        if getattr(folder, 'is_locked', False): indicators.append("lock")
        
        icon_color = "white" if self.theme_mode == "dark" else None
        item.setIcon(0, get_combined_indicators(indicators, color=icon_color))
        return item

    def on_item_clicked(self, item, column):
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data: return
        
        if isinstance(data, str) and data.startswith("NOTEBOOK:"):
            nb_id = data.split(":")[1]
            # Switch the selector to this notebook for a cleaner view
            idx = self.nb_selector.findData(nb_id)
            if idx >= 0:
                self.nb_selector.setCurrentIndex(idx)
            return
            
        if data == "ARCHIVED_ROOT":
            item.setExpanded(not item.isExpanded())
            return
            
        # Emit folder selection
        self.folderSelected.emit(data)

    def on_rows_moved(self, parent, start, end, dest_parent, dest_row):
        pass # Placeholder for Drag & Drop reordering if implemented for Tree

    def prompt_new_folder(self, notebook_id=None):
        """Prompt for folder name. Use provided ID or current dropdown selection."""
        # Force notebook_id if not provided
        if not notebook_id:
            notebook_id = self.nb_selector.currentData()
            
        if not notebook_id and self.all_notebooks:
            notebook_id = self.all_notebooks[0].id
            
        if not notebook_id:
            QMessageBox.warning(self, "No Notebook", "Please create or select a notebook first.")
            return
            
        name, ok = ZenInputDialog.getText(self, "New Folder", "Folder Name:")
        if ok and name:
            self.createFolder.emit(name, notebook_id)

    def prompt_new_notebook(self):
        name, ok = ZenInputDialog.getText(self, "New Notebook", "Main Notebook Name:")
        if ok and name:
            self.createNotebook.emit(name)

    def prompt_rename_notebook(self, nb_id, current_name):
        # Strip numbering from name
        clean_name = current_name.split(". ", 1)[-1] if ". " in current_name else current_name
        name, ok = ZenInputDialog.getText(self, "Rename Notebook", "Notebook Name:", text=clean_name)
        if ok and name:
            # Simple handling: update in-memory and sidebar will refresh via MainWindow
            nb = next((n for n in self.all_notebooks if n.id == nb_id), None)
            if nb:
                nb.name = name
                self.refresh_list()
                # Need a signal to persist this
                self.updateFolder.emit("ROOT", {"notebook_rename": (nb_id, name)})

    def confirm_delete_notebook(self, nb_id):
        nb = next((n for n in self.all_notebooks if n.id == nb_id), None)
        if not nb: return
        
        # Type to confirm dialog
        name_to_type = nb.name.strip()
        msg = f"This will PERMANENTLY delete the notebook <b>'{name_to_type}'</b>.<br><br>Please type the name of the notebook exactly to confirm:"
        
        typed_name, ok = ZenInputDialog.getText(self, "Confirm Critical Deletion", msg)
        
        if ok:
            if typed_name.strip() == name_to_type:
                self.deleteNotebook.emit(nb_id)
            else:
                QMessageBox.warning(self, "Incorrect Name", "The name entered did not match. Deletion cancelled.")

    def prompt_rename_folder(self, folder_id, current_name):
        name, ok = ZenInputDialog.getText(self, "Rename Folder", "Folder Name:", text=current_name)
        if ok and name:
            self.renameFolder.emit(folder_id, name)

    def prompt_change_color(self, folder_id):
        folder = next((f for f in self.all_folders if f.id == folder_id), None)
        if not folder: return
        from PyQt6.QtGui import QColor
        initial_color = getattr(folder, 'color', '#FFFFFF') or '#FFFFFF'
        initial = QColor(initial_color)
        color = QColorDialog.getColor(initial, self, "Select Folder Color")
        if color.isValid(): self.updateFolder.emit(folder_id, {"color": color.name()})

    def show_context_menu(self, pos):
        item = self.list_widget.itemAt(pos)
        if not item: return

        data = item.data(0, Qt.ItemDataRole.UserRole)
        menu = QMenu()
        menu.setStyleSheet("QMenu { menu-scrollable: 1; }")

        if isinstance(data, str) and data.startswith("NOTEBOOK:"):
            nb_id = data.split(":")[1]
            add_action = menu.addAction(get_premium_icon("folder_add"), "Add Folder Here")
            rename_action = menu.addAction(get_premium_icon("edit"), "Rename Notebook")
            delete_action = menu.addAction(get_premium_icon("delete"), "Delete Notebook")
            
            action = menu.exec(self.list_widget.mapToGlobal(pos))
            if action == add_action:
                self.prompt_new_folder(nb_id)
            elif action == rename_action:
                self.prompt_rename_notebook(nb_id, item.text(0))
            elif action == delete_action:
                self.confirm_delete_notebook(nb_id)
            return

        # Folder Context Menu (Standard)
        if data in ["ALL_NOTEBOOKS_ROOT", "ARCHIVED_ROOT"]:
            return

        folder_id = data
        folder = next((f for f in self.all_folders if f.id == folder_id), None)
        if not folder: return

        # Reproduce existing folder options
        rename_act = menu.addAction(get_premium_icon("edit"), "Rename Folder")
        # Reproduce existing folder options
        rename_act = menu.addAction(get_premium_icon("edit"), "Rename Folder")
        
        set_cover_act = menu.addAction(get_premium_icon("image"), "Set Cover Image...")
        edit_desc_act = menu.addAction(get_premium_icon("align_left"), "Edit Description...")

        color_act = menu.addAction(get_premium_icon("palette"), "Change Color")
        
        # Priority Submenu
        prio_menu = menu.addMenu(get_premium_icon("flag"), "Set Priority")
        p0 = prio_menu.addAction("None")
        p1 = prio_menu.addAction("❶ High")
        p2 = prio_menu.addAction("❷ Medium")
        p3 = prio_menu.addAction("❸ Low")

        pin_text = "Remove from Favorites" if folder.is_pinned else "Add to Favorites"
        pin_icon = "heart_off" if folder.is_pinned else "heart"
        # Fallback if heart_off not exists, use heart
        pin_act = menu.addAction(get_premium_icon("heart"), pin_text)
        
        arch_text = "Unarchive Folder" if folder.is_archived else "Archive Folder"
        arch_act = menu.addAction(get_premium_icon("folder_archived"), arch_act_text := arch_text) # Fix for name overlap
        
        menu.addSeparator()
        export_act = menu.addAction(get_premium_icon("export"), "Export Folder to PDF")
        
        menu.addSeparator()
        delete_act = menu.addAction(get_premium_icon("delete"), "Delete Folder")

        action = menu.exec(self.list_widget.mapToGlobal(pos))
        if action == rename_act:
            self.prompt_rename_folder(folder_id, folder.name)
        elif action == set_cover_act:
            path, _ = QFileDialog.getOpenFileName(self, "Select Cover Image", "", "Images (*.png *.jpg *.jpeg *.webp)")
            if path: self.updateFolder.emit(folder_id, {"cover_image": path})
        elif action == edit_desc_act:
            desc, ok = ZenInputDialog.getText(self, "Edit Description", "Description:", text=getattr(folder, 'description', "") or "")
            if ok: self.updateFolder.emit(folder_id, {"description": desc})
        elif action == color_act:
            self.prompt_change_color(folder_id)
        elif action == pin_act:
            self.updateFolder.emit(folder_id, {"is_pinned": not folder.is_pinned})
        elif action == arch_act:
            self.updateFolder.emit(folder_id, {"is_archived": not folder.is_archived})
        elif action == export_act:
            self.exportFolder.emit(folder_id)
        elif action == delete_act:
            self.deleteFolder.emit(folder_id)
        elif action in [p0, p1, p2, p3]:
            p_val = [p0, p1, p2, p3].index(action)
            self.updateFolder.emit(folder_id, {"priority": p_val})

    def select_folder_by_id(self, folder_id):
        self.list_widget.clearSelection()
        from PyQt6.QtWidgets import QTreeWidgetItemIterator
        iterator = QTreeWidgetItemIterator(self.list_widget)
        while iterator.value():
            item = iterator.value()
            if item.data(0, Qt.ItemDataRole.UserRole) == folder_id:
                self.list_widget.setCurrentItem(item)
                if item.parent():
                    item.parent().setExpanded(True)
                break
            iterator += 1

    def toggle_archived_view(self):
        self.showing_archived = not self.showing_archived
        # Update UI if needed, refresh list
        self.refresh_list()
