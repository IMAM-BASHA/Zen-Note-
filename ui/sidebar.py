from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, 
    QPushButton, QMenu, QInputDialog, QMessageBox, QLabel, QFrame,
    QLineEdit, QColorDialog, QTreeWidget, QTreeWidgetItem, QHeaderView,
    QComboBox, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QPoint
from ui.color_delegate import ColorDelegate, COLOR_ROLE
from util.icon_factory import get_premium_icon, get_combined_indicators

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
        header_layout = QVBoxLayout(header_container)
        header_layout.setContentsMargins(10, 15, 10, 10)
        header_layout.setSpacing(10)
        
        title_row = QWidget()
        title_layout = QHBoxLayout(title_row)
        title_layout.setContentsMargins(0,0,0,0)
        
        self.back_btn = QPushButton()
        self.back_btn.setIcon(get_premium_icon("back"))
        self.back_btn.setToolTip("Back to Main List")
        self.back_btn.setFixedSize(30, 24)
        self.back_btn.clicked.connect(self.toggle_archived_view)
        self.back_btn.setVisible(False)
        title_layout.addWidget(self.back_btn)

        # Notebook Selector Dropdown
        self.nb_selector = QComboBox()
        self.nb_selector.setObjectName("SidebarNotebookSelector")
        
        # Allow it to expand and elide long text
        self.nb_selector.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # Improve popup display
        view = self.nb_selector.view()
        view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        view.setWordWrap(True)
        view.setMinimumWidth(300)
        view.setStyleSheet("""
            QListView { outline: 0; padding: 5px; background: white; } 
            QListView::item { padding: 10px 5px; border-bottom: 1px solid #f0f0f0; min-height: 30px; }
            QListView::item:hover { background: #f5f5f5; }
        """)
        
        self.nb_selector.setCursor(Qt.CursorShape.PointingHandCursor)
        # Initial styling will be set via set_theme_mode
        self.nb_selector.currentIndexChanged.connect(self.on_notebook_changed)
        title_layout.addWidget(self.nb_selector, 1) # Give it stretch
        
        header_layout.addWidget(title_row)

        # Row 2: Actions & Utilities
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(6)

        # Primary Actions (Moved to Row 2)
        self.add_folder_btn = QPushButton()
        self.add_folder_btn.setIcon(get_premium_icon("plus", color="white"))
        self.add_folder_btn.setFixedSize(28, 28)
        self.add_folder_btn.setToolTip("Create New Main Notebook")
        self.add_folder_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_folder_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078D7;
                border-radius: 4px;
                padding: 4px;
            }
            QPushButton:hover { background-color: #005A9E; }
        """)
        self.add_folder_btn.clicked.connect(self.prompt_new_notebook)
        button_layout.addWidget(self.add_folder_btn)

        self.lock_btn = QPushButton()
        self.lock_btn.setIcon(get_premium_icon("unlock", color="white"))
        self.lock_btn.setToolTip("Lock navigation and editing")
        self.lock_btn.setCheckable(True)
        self.lock_btn.setFixedSize(28, 28)
        self.lock_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lock_btn.setStyleSheet("""
            QPushButton {
                background-color: #455A64;
                border-radius: 4px;
                padding: 4px;
            }
            QPushButton:checked { background-color: #D32F2F; }
        """)
        self.lock_btn.toggled.connect(self._on_lock_toggled)
        button_layout.addWidget(self.lock_btn)

        self.delete_nb_btn = QPushButton()
        self.delete_nb_btn.setIcon(get_premium_icon("trash", color="white"))
        self.delete_nb_btn.setFixedSize(28, 28)
        self.delete_nb_btn.setToolTip("Delete Current Notebook")
        self.delete_nb_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.delete_nb_btn.setStyleSheet("""
            QPushButton {
                background-color: #D32F2F;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton:hover { background-color: #B71C1C; }
        """)
        self.delete_nb_btn.clicked.connect(self._on_delete_notebook_clicked)
        button_layout.addWidget(self.delete_nb_btn)

        button_layout.addSpacing(10)

        # Utility Buttons (Restored)
        self.theme_btn = QPushButton() 
        self.theme_btn.setToolTip("Toggle Dark/Light Mode")
        self.theme_btn.setFixedSize(28, 28)
        self.theme_btn.setIconSize(QSize(18, 18))
        self.theme_btn.clicked.connect(self.toggleTheme.emit)
        button_layout.addWidget(self.theme_btn)

        self.highlight_preview_btn = QPushButton()
        self.highlight_preview_btn.setIcon(get_premium_icon("bookmark"))
        self.highlight_preview_btn.setToolTip("Preview Highlighted Text")
        self.highlight_preview_btn.setFixedSize(28, 28)
        self.highlight_preview_btn.setIconSize(QSize(18, 18))
        self.highlight_preview_btn.clicked.connect(self.requestHighlightPreview.emit)
        button_layout.addWidget(self.highlight_preview_btn)
        
        self.preview_btn = QPushButton()
        self.preview_btn.setIcon(get_premium_icon("eye"))
        self.preview_btn.setToolTip("Preview Folder PDF")
        self.preview_btn.setFixedSize(28, 28)
        self.preview_btn.setIconSize(QSize(18, 18))
        self.preview_btn.clicked.connect(self.requestPdfPreview.emit)
        button_layout.addWidget(self.preview_btn)
        
        self.sort_btn = QPushButton()
        self.sort_btn.setIcon(get_premium_icon("sort_down"))
        self.sort_btn.setToolTip("Sort by Date (Newest First)")
        self.sort_btn.setFixedSize(28, 28)
        self.sort_btn.setIconSize(QSize(18, 18))
        self.sort_btn.setCheckable(True)
        self.sort_btn.setChecked(True)
        self.sort_btn.clicked.connect(self.toggle_sort)
        button_layout.addWidget(self.sort_btn)
        
        self.wrap_btn = QPushButton()
        self.wrap_btn.setIcon(get_premium_icon("wrap"))
        self.wrap_btn.setToolTip("Toggle Text Wrap")
        self.wrap_btn.setFixedSize(28, 28)
        self.wrap_btn.setIconSize(QSize(18, 18))
        self.wrap_btn.setCheckable(True)
        self.wrap_btn.clicked.connect(lambda: self.wrapToggled.emit(self.wrap_btn.isChecked()))
        button_layout.addWidget(self.wrap_btn)
        
        button_layout.addStretch()

        # Add row to header layout
        header_layout.addWidget(button_container)
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
        text_color = "#FFFFFF" if is_dark else "#202124"
        icon_color = "#FFFFFF" if is_dark else "#444444"
        
        # 1. Update Notebook Selector Styling
        self.nb_selector.setStyleSheet(f"""
            QComboBox {{
                font-size: 15px;
                font-weight: 900;
                color: {text_color};
                border: none;
                background: transparent;
                padding: 4px 25px 4px 2px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
                subcontrol-origin: padding;
                subcontrol-position: center right;
            }}
            QComboBox::down-arrow {{
                image: url(util/icons/chevron-down.png);
                width: 12px;
                height: 12px;
            }}
            QComboBox:hover {{
                color: #0078D7;
                background-color: rgba(0, 120, 215, 0.05);
                border-radius: 4px;
            }}
        """)
        
        # 1.1 Force Tree Widget Text Color
        self.list_widget.setStyleSheet(f"""
            QTreeWidget {{
                background-color: transparent;
                color: {text_color};
                border: none;
            }}
            QTreeWidget::item {{
                color: {text_color};
                padding: 5px;
            }}
            QTreeWidget::item:selected {{
                background-color: {'#4A90E2' if is_dark else '#E0E0E0'};
                color: {'white' if is_dark else 'black'};
            }}
        """)
        
        # 2. Refresh Icons
        self.theme_btn.setIcon(get_premium_icon("sun" if is_dark else "moon", color=icon_color))
        self.highlight_preview_btn.setIcon(get_premium_icon("bookmark", color=icon_color))
        self.preview_btn.setIcon(get_premium_icon("eye", color=icon_color))
        self.wrap_btn.setIcon(get_premium_icon("wrap", color=icon_color))
        self.back_btn.setIcon(get_premium_icon("back", color=icon_color))
        
        # Sort icon
        sort_icon = "sort_up" if not self.sort_descending else "sort_down"
        self.sort_btn.setIcon(get_premium_icon(sort_icon, color=icon_color))
        
        # Action Icons (Always white as they have high-contrast backgrounds)
        self.add_folder_btn.setIcon(get_premium_icon("plus", color="white"))
        self.lock_btn.setIcon(get_premium_icon("lock" if self.lock_btn.isChecked() else "unlock", color="white"))
        self.delete_nb_btn.setIcon(get_premium_icon("trash", color="white"))
        
        # 3. Refresh Tree Items (to update folder icons)
        self.theme_mode = mode
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
        selected_nb_id = self.nb_selector.currentData()
        self.list_widget.clear()

        # 1. Total Notebooks Root (Global View) - REMOVED (Handled by Dropdown)

        # 2. Scoped Archived Root Item
        if not self.showing_archived and not search_text:
            nb = next((n for n in self.all_notebooks if n.id == selected_nb_id), None)
            if nb:
                # Get current notebook's folders
                archived_count = 0
                for f in self.all_folders:
                    if f.id in nb.folder_ids and getattr(f, 'is_archived', False):
                        archived_count += 1
                        
                if archived_count > 0:
                    icon_color = "white" if self.theme_mode == "dark" else None
                    arch_item = QTreeWidgetItem([f" Archived ({archived_count})"])
                    arch_item.setIcon(0, get_premium_icon("folder_archived", color=icon_color))
                    arch_item.setData(0, Qt.ItemDataRole.UserRole, "ARCHIVED_ROOT")
                    font = arch_item.font(0)
                    font.setBold(True)
                    arch_item.setFont(0, font)
                    self.list_widget.addTopLevelItem(arch_item)

        # 3. Filter Folders
        # 3. Filter Folders by Notebook and Archive Status
        nb = next((n for n in self.all_notebooks if n.id == selected_nb_id), None)
        nb_folder_ids = nb.folder_ids if nb else []
        
        if self.showing_archived:
            filtered_folders = [f for f in self.all_folders if f.id in nb_folder_ids and getattr(f, 'is_archived', False)]
        else:
            filtered_folders = [f for f in self.all_folders if f.id in nb_folder_ids and not getattr(f, 'is_archived', False)]
            
        if search_text:
            filtered_folders = [f for f in filtered_folders if search_text in f.name.lower()]
        
        # Sort Folders
        def sort_key(f):
            pinned_rank = not f.is_pinned
            prio = f.priority if f.priority > 0 else 999
            order_rank = getattr(f, 'order', 0)
            return (pinned_rank, prio, order_rank)
        
        filtered_folders.sort(key=sort_key)

        # Map for quick lookup
        folder_map = {f.id: f for f in filtered_folders}

        # 4. Populate Folders for the selected notebook
        if not self.showing_archived:
            # Sequential numbering for folders
            for i, folder in enumerate(filtered_folders, 1):
                f_item = self._create_folder_item(folder, index=i)
                self.list_widget.addTopLevelItem(f_item)
        else:
            # Simple list for Archived View (with numbering)
            for i, folder in enumerate(filtered_folders, 1):
                f_item = self._create_folder_item(folder, index=i)
                self.list_widget.addTopLevelItem(f_item)

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
            self.toggle_archived_view()
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
            
        name, ok = QInputDialog.getText(self, "New Folder", "Folder Name:")
        if ok and name:
            self.createFolder.emit(name, notebook_id)

    def prompt_new_notebook(self):
        name, ok = QInputDialog.getText(self, "New Notebook", "Main Notebook Name:")
        if ok and name:
            self.createNotebook.emit(name)

    def prompt_rename_notebook(self, nb_id, current_name):
        # Strip numbering from name
        clean_name = current_name.split(". ", 1)[-1] if ". " in current_name else current_name
        name, ok = QInputDialog.getText(self, "Rename Notebook", "Notebook Name:", text=clean_name)
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
        
        typed_name, ok = QInputDialog.getText(self, "Confirm Critical Deletion", msg)
        
        if ok:
            if typed_name.strip() == name_to_type:
                self.deleteNotebook.emit(nb_id)
            else:
                QMessageBox.warning(self, "Incorrect Name", "The name entered did not match. Deletion cancelled.")

    def prompt_rename_folder(self, folder_id, current_name):
        name, ok = QInputDialog.getText(self, "Rename Folder", "Folder Name:", text=current_name)
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
        color_act = menu.addAction(get_premium_icon("palette"), "Change Color")
        
        # Priority Submenu
        prio_menu = menu.addMenu(get_premium_icon("flag"), "Set Priority")
        p0 = prio_menu.addAction("None")
        p1 = prio_menu.addAction("❶ High")
        p2 = prio_menu.addAction("❷ Medium")
        p3 = prio_menu.addAction("❸ Low")

        pin_text = "Unpin Folder" if folder.is_pinned else "Pin Folder"
        pin_act = menu.addAction(get_premium_icon("pin"), pin_text)
        
        arch_text = "Unarchive Folder" if folder.is_archived else "Archive Folder"
        arch_act = menu.addAction(get_premium_icon("folder_archived"), arch_text)
        
        menu.addSeparator()
        export_act = menu.addAction(get_premium_icon("export"), "Export Folder to PDF")
        
        menu.addSeparator()
        delete_act = menu.addAction(get_premium_icon("delete"), "Delete Folder")

        action = menu.exec(self.list_widget.mapToGlobal(pos))
        if action == rename_act:
            self.prompt_rename_folder(folder_id, folder.name)
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
