from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, 
    QPushButton, QLabel, QMessageBox, QWidget
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QFont

class MoveNoteDialog(QDialog):
    def __init__(self, parent, notes, all_folders, current_folder_id):
        super().__init__(parent)
        self.setWindowTitle("Move Note to Folder")
        self.setMinimumWidth(450)
        self.setMinimumHeight(500)
        
        self.notes = notes
        self.all_folders = all_folders
        self.current_folder_id = current_folder_id
        self.target_folder_id = None
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 1. Header Section
        header_layout = QVBoxLayout()
        header_layout.setSpacing(5)
        
        title = QLabel("Move Notes")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        header_layout.addWidget(title)
        
        # Dynamic description
        if len(self.notes) == 1:
            desc_text = f"Select a destination for: <b>{self.notes[0].title}</b>"
        else:
            desc_text = f"Select a destination for <b>{len(self.notes)} notes</b>"
            
        desc = QLabel(desc_text)
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #666; font-size: 14px;")
        desc.setTextFormat(Qt.TextFormat.RichText)
        header_layout.addWidget(desc)
        
        layout.addLayout(header_layout)
        
        # 2. Folder List
        self.folder_list = QListWidget()
        self.folder_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.folder_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 5px;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #007ACC;
                color: white;
            }
            QListWidget::item:disabled {
                background-color: transparent;
                color: #888;
                font-weight: bold;
                padding-top: 15px;
                padding-bottom: 5px;
                border-bottom: 1px solid #eee;
            }
        """)
        
        self.populate_folders()
        self.folder_list.itemDoubleClicked.connect(self.accept_selection)
        layout.addWidget(self.folder_list)
        
        # 3. Footer / Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.setFixedSize(100, 36)
        self.cancel_btn.clicked.connect(self.reject)
        
        self.move_btn = QPushButton("Move Here")
        self.move_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.move_btn.setFixedSize(120, 36)
        self.move_btn.setDefault(True)
        self.move_btn.setStyleSheet("""
            QPushButton {
                background-color: #007ACC;
                color: white;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #008AD8;
            }
            QPushButton:msgbox-default { /* Default styling */
                padding: 6px 12px;
            }
        """)
        self.move_btn.clicked.connect(self.accept_selection)
        
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.move_btn)
        
        layout.addLayout(btn_layout)
        
    def populate_folders(self):
        # Separate folders
        active_folders = []
        archived_folders = []
        
        for folder in self.all_folders:
            if folder.id == self.current_folder_id:
                continue
            
            if getattr(folder, 'is_archived', False):
                archived_folders.append(folder)
            else:
                active_folders.append(folder)
                
        # Helper to add section header
        def add_header(text):
            item = QListWidgetItem(text)
            item.setFlags(Qt.ItemFlag.NoItemFlags) # Not selectable
            item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)
            self.folder_list.addItem(item)
            
        # Helper to add folder item
        def add_folder_item(folder):
            count = len(folder.notes)
            text = f"{folder.name} ({count} notes)"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, folder.id)
            
            # Optional: Set icon based on folder type or color
            # if folder.color: ...
            
            self.folder_list.addItem(item)

        # Populate Active
        if active_folders:
            add_header("AVAILABLE FOLDERS")
            for f in active_folders:
                add_folder_item(f)
                
        # Populate Archived
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
            # If nothing selected, maybe check specific flags but generally return
            return
            
        item = selected_items[0]
        # Ensure it's not a header (though headers usually not selectable with current flags)
        folder_id = item.data(Qt.ItemDataRole.UserRole)
        
        if folder_id:
            self.target_folder_id = folder_id
            self.accept()
