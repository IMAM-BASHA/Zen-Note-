from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, 
    QPushButton, QLabel, QMessageBox, QWidget
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QFont
import ui.styles as styles
from ui.zen_dialog import ZenDialog

class MoveNoteDialog(ZenDialog):
    def __init__(self, parent, notes, all_folders, current_folder_id):
        # Auto-detect theme
        theme_mode = "light"
        if parent and hasattr(parent, 'theme_mode'):
            theme_mode = parent.theme_mode
        elif parent and hasattr(parent, 'data_manager'):
            theme_mode = parent.data_manager.get_setting("theme_mode", "light")

        super().__init__(parent, title="Move Notes", theme_mode=theme_mode)
        self.notes = notes
        self.all_folders = all_folders
        self.current_folder_id = current_folder_id
        self.target_folder_id = None
        
        self.setMinimumWidth(450)
        self.setMinimumHeight(550)
            
        self.setup_ui_local()
        self.apply_theme_local()
        
    def setup_ui_local(self):
        # Description
        if len(self.notes) == 1:
            desc_text = f"Select destination for: <b>{self.notes[0].title}</b>"
        else:
            desc_text = f"Select destination for <b>{len(self.notes)} notes</b>"
            
        self.desc = QLabel(desc_text)
        self.desc.setWordWrap(True)
        self.desc.setTextFormat(Qt.TextFormat.RichText)
        self.desc.setStyleSheet("color: gray; font-size: 11px;")
        self.content_layout.addWidget(self.desc)
        
        # 2. Folder List
        self.folder_list = QListWidget()
        self.folder_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.populate_folders()
        self.folder_list.itemDoubleClicked.connect(self.accept_selection)
        self.content_layout.addWidget(self.folder_list)
        
        # 3. Footer / Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.clicked.connect(self.reject)
        
        self.move_btn = QPushButton("Move Here")
        self.move_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.move_btn.setDefault(True)
        self.move_btn.clicked.connect(self.accept_selection)
        
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.move_btn)
        self.content_layout.addLayout(btn_layout)
        
    def populate_folders(self):
        active_folders = []
        archived_folders = []
        
        for folder in self.all_folders:
            if folder.id == self.current_folder_id:
                continue
            if getattr(folder, 'is_archived', False):
                archived_folders.append(folder)
            else:
                active_folders.append(folder)
                
        def add_header(text):
            item = QListWidgetItem(text)
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)
            self.folder_list.addItem(item)
            
        def add_folder_item(folder):
            count = len(folder.notes)
            text = f"{folder.name} ({count} notes)"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, folder.id)
            self.folder_list.addItem(item)

        if active_folders:
            add_header("AVAILABLE FOLDERS")
            for f in active_folders:
                add_folder_item(f)
                
        if archived_folders:
            add_header("ARCHIVED FOLDERS")
            for f in archived_folders:
                add_folder_item(f)
                
        if not active_folders and not archived_folders:
            item = QListWidgetItem("No other folders available")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.folder_list.addItem(item)
            self.move_btn.setEnabled(False)

    def accept_selection(self):
        selected_items = self.folder_list.selectedItems()
        if not selected_items:
            return
        item = selected_items[0]
        folder_id = item.data(Qt.ItemDataRole.UserRole)
        if folder_id:
            self.target_folder_id = folder_id
            self.accept()

    def apply_theme_local(self):
        c = styles.ZEN_THEME.get(self.theme_mode, styles.ZEN_THEME["light"])
        
        self.folder_list.setStyleSheet(f"""
            QListWidget {{
                border: 1px solid {c['border']};
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                background-color: {c['background']};
                color: {c['foreground']};
                outline: none;
            }}
            QListWidget::item {{
                padding: 10px;
                border-radius: 6px;
                color: {c['foreground']};
            }}
            QListWidget::item:selected {{
                background-color: {c['active_item_bg']};
                color: {c['primary']};
                font-weight: bold;
            }}
            QListWidget::item:disabled {{
                color: {c['muted_foreground']};
                font-weight: bold;
                padding-top: 15px;
                padding-bottom: 5px;
                border-bottom: 1px solid {c['border']};
            }}
        """)
        
        btn_base = f"""
            QPushButton {{
                padding: 8px 18px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }}
        """
        self.cancel_btn.setStyleSheet(btn_base + f"""
            QPushButton {{
                background-color: transparent;
                color: {c['foreground']};
                border: 1px solid {c['border']};
            }}
            QPushButton:hover {{ background-color: {c['muted']}; }}
        """)
        
        self.move_btn.setStyleSheet(btn_base + f"""
            QPushButton {{
                background-color: {c['primary']};
                color: {c['primary_foreground']};
                border: none;
            }}
            QPushButton:hover {{ opacity: 0.9; }}
            QPushButton:disabled {{
                background-color: {c['muted']};
                color: {c['muted_foreground']};
            }}
        """)
