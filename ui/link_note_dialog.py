from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QTreeWidget, QTreeWidgetItem, QPushButton, QDialogButtonBox,
    QWidget, QFrame, QTabWidget, QCheckBox
)
from datetime import datetime
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QFont, QColor
from util.icon_factory import get_premium_icon
import ui.styles as styles

class LinkNoteDialog(QDialog):
    """Dialog to search and select a note to link to, grouped by folder."""
    
    def __init__(self, parent=None, data_manager=None, current_note_id=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self.current_note_id = current_note_id 
        self.selected_note_id = None
        self.selected_note_title = None
        self.open_in_overlay = False
        
        self.setWindowTitle("Link to Note")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        self.resize(600, 500)
        
        # Apply Theme if available
        self.theme_mode = "light"
        if parent and hasattr(parent, 'theme_mode'):
            self.theme_mode = parent.theme_mode
            
        self._setup_ui()
        self._load_notes()
        self._apply_theme()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        lbl_header = QLabel("Select a note to link")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        lbl_header.setFont(font)
        layout.addWidget(lbl_header)
        
        # Search Bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search notes...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._filter_notes)
        layout.addWidget(self.search_input)
        
        # Tabs
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Active Tree
        self.active_tree = self._create_tree()
        self.tabs.addTab(self.active_tree, "Active Notes")
        

        # Archive Tree
        self.archive_tree = self._create_tree()
        self.tabs.addTab(self.archive_tree, "Archived Notes")
        
        # Options
        self.cb_overlay = QCheckBox("Open in Overlay")
        self.cb_overlay.setToolTip("Open this link in a floating overlay window instead of navigating")
        self.cb_overlay.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self.cb_overlay)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.btn_link = QPushButton("Insert Link")
        self.btn_link.clicked.connect(self._on_accept)
        self.btn_link.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_link.setDefault(True)
        self.btn_link.setEnabled(False) 
        
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_link)
        layout.addLayout(btn_layout)

    def _create_tree(self):
        tree = QTreeWidget()
        tree.setHeaderHidden(True)
        tree.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        tree.setIndentation(20)
        tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        tree.itemSelectionChanged.connect(lambda: self._on_selection_changed(tree))
        return tree

    def _load_notes(self):
        """Load notes grouped by folder into respective tabs."""
        self.active_tree.clear()
        self.archive_tree.clear()
        
        if not self.data_manager:
            return
            
        # Separate Folders
        active_folders = [f for f in self.data_manager.folders if not getattr(f, 'is_archived', False)]
        archived_folders = [f for f in self.data_manager.folders if getattr(f, 'is_archived', False)]
        
        # Sort Logic (Sidebar Match)
        def sidebar_sort_key(f):
            pinned_rank = not f.is_pinned
            prio = f.priority if f.priority > 0 else 999
            order_rank = getattr(f, 'order', 0)
            try:
                dt = datetime.fromisoformat(f.created_at)
                timestamp = dt.timestamp()
            except:
                timestamp = 0
            date_rank = -timestamp 
            return (pinned_rank, prio, order_rank, date_rank)

        active_folders.sort(key=sidebar_sort_key)
        archived_folders.sort(key=lambda f: f.name.lower()) # Archived A-Z

        # 1. Populate Active Tree
        for i, folder in enumerate(active_folders, 1):
            self._add_folder_item(folder, self.active_tree.invisibleRootItem(), index_prefix=i)
            
        # 2. Populate Archive Tree
        for folder in archived_folders:
            self._add_folder_item(folder, self.archive_tree.invisibleRootItem(), is_archived=True)

    def _add_folder_item(self, folder, parent_item, is_archived=False, index_prefix=None):
        """Helper to create folder hierarchy."""
        valid_notes = [n for n in folder.notes if n.id != self.current_note_id]
        
        # Construct Display Name
        display_name = folder.name
        if index_prefix is not None:
             display_name = f"{index_prefix}. {folder.name}"
             
        if folder.is_pinned:
             display_name = "📌 " + display_name
        
        folder_item = QTreeWidgetItem(parent_item)
        folder_item.setText(0, display_name)
        folder_item.setIcon(0, get_premium_icon("folder_open" if not is_archived else "folder_archived"))
        folder_item.setData(0, Qt.ItemDataRole.UserRole, "FOLDER")
        folder_item.setFlags(Qt.ItemFlag.ItemIsEnabled) # Folders not selectable
        folder_item.setExpanded(False) # Collapsed by default
        
        for note in valid_notes:
            note_item = QTreeWidgetItem(folder_item)
            note_item.setText(0, note.title)
            note_item.setIcon(0, get_premium_icon("note"))
            note_item.setData(0, Qt.ItemDataRole.UserRole, note.id)     # Note ID
            note_item.setData(0, Qt.ItemDataRole.UserRole + 1, note.title) # Note Title

    def _filter_notes(self, text):
        """Filter tree items in BOTH trees."""
        text = text.lower().strip()
        
        def filter_tree(tree):
            def check_item(item):
                has_visible_child = False
                item_text = item.text(0).lower()
                
                for i in range(item.childCount()):
                    if check_item(item.child(i)):
                        has_visible_child = True
                
                item_type = item.data(0, Qt.ItemDataRole.UserRole)
                is_folder = (item_type == "FOLDER")
                
                matches = text in item_text
                should_show = True if not text else (matches or has_visible_child if is_folder else matches)
                
                item.setHidden(not should_show)
                if should_show and text:
                    item.setExpanded(True)
                return should_show

            root = tree.invisibleRootItem()
            for i in range(root.childCount()):
                check_item(root.child(i))

        filter_tree(self.active_tree)
        filter_tree(self.archive_tree)

    def _on_selection_changed(self, tree):
        # Enforce single selection across tabs?
        # If user selects in Active, we might want to allow it.
        # But for "Insert Link", we need ONE target.
        
        # If this tree has selection, clear/ignore others?
        # to visualy indicate exclusivity
        if tree == self.active_tree:
             self.archive_tree.blockSignals(True)
             self.archive_tree.clearSelection()
             self.archive_tree.blockSignals(False)
        else:
             self.active_tree.blockSignals(True)
             self.active_tree.clearSelection()
             self.active_tree.blockSignals(False)


        items = tree.selectedItems()
        valid_selection = False
        if items:
            item = items[0]
            data = item.data(0, Qt.ItemDataRole.UserRole)
            if data and data != "FOLDER":
                 self.selected_note_id = data
                 self.selected_note_title = item.data(0, Qt.ItemDataRole.UserRole + 1)
                 valid_selection = True
        
        self.btn_link.setEnabled(valid_selection)
        if not valid_selection:
            self.selected_note_id = None
            self.selected_note_title = None

    def _on_item_double_clicked(self, item, column):
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data and data != "FOLDER":
            self.selected_note_id = data
            self.selected_note_title = item.data(0, Qt.ItemDataRole.UserRole + 1)
            self._on_accept()

    def _on_accept(self):
        self.open_in_overlay = self.cb_overlay.isChecked()
        self.accept()

    def _apply_theme(self):
        """Apply styles based on theme."""
        c = styles.ZEN_THEME.get(self.theme_mode, styles.ZEN_THEME["light"])
        is_dark = self.theme_mode == "dark"
            
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {c['background']};
                color: {c['foreground']};
            }}
            QLabel {{
                color: {c['foreground']};
            }}
            QLineEdit {{
                background-color: {c['background']};
                color: {c['foreground']};
                border: 1px solid {c['input']};
                border-radius: 4px;
                padding: 6px;
                font-size: 14px;
            }}
            QTreeWidget {{
                background-color: {c['background']};
                color: {c['foreground']};
                border: 1px solid {c['border']};
                border-radius: 4px;
                font-size: 14px;
                outline: none;
            }}
            QTreeWidget::item {{
                padding: 6px;
            }}
            QTreeWidget::item:hover {{
                background-color: {c['muted']};
            }}
            QTreeWidget::item:selected {{
                background-color: {c['accent']};
                color: {c['accent_foreground']}; 
            }}
            QTreeWidget::branch:has-children:!has-siblings:closed,
            QTreeWidget::branch:closed:has-children:has-siblings {{
                border-image: none;
                image: none; 
            }}
            QTabWidget::pane {{
                border: 1px solid {c['border']};
                border-radius: 4px;
                top: -1px; 
            }}
            QTabBar::tab {{
                background: {c['background']};
                border: 1px solid {c['border']};
                padding: 8px 12px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                color: {c['foreground']};
            }}
            QTabBar::tab:selected {{
                background: {c['background']};
                border-bottom-color: {c['background']}; /* Blend with pane */
                font-weight: bold;
            }}
            QPushButton {{
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 13px;
            }}
        """)
        
        self.btn_link.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['primary']};
                color: {c['primary_foreground']};
                border: none;
            }}
            QPushButton:hover {{
                opacity: 0.9;
            }}
            QPushButton:disabled {{
                background-color: {c['muted']};
                color: {c['muted_foreground']};
            }}
        """)
        
        self.btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {c['foreground']};
                border: 1px solid {c['input']};
            }}
            QPushButton:hover {{
                background-color: {c['muted']};
            }}
        """)
