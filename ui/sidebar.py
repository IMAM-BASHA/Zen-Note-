from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, 
    QLineEdit, QPushButton, QHBoxLayout, QMenu, QMessageBox, QFileDialog,
    QFrame, QLabel, QComboBox, QSizePolicy, QColorDialog, QStackedWidget,
    QListWidget, QListWidgetItem, QStyledItemDelegate, QStyle
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QRect, QRectF
from PyQt6.QtGui import QFont, QColor, QAction, QPainter, QIcon, QBrush, QPen, QPainterPath
from ui.color_delegate import ColorDelegate, COLOR_ROLE
import ui.styles as styles
from util.icon_factory import get_premium_icon, get_combined_indicators
from ui.zen_dialog import ZenInputDialog
from ui.theme_chooser import ThemeChooserDialog
from ui.focus_mode import FocusModeDialog
from ui.animations import pulse_button

VIEW_MODE_LIST = "list"
VIEW_MODE_GRID = "grid"

class FolderCardDelegate(QStyledItemDelegate):
    def __init__(self, parent=None, theme_mode="light"):
        super().__init__(parent)
        self.theme_mode = theme_mode

    def set_theme_mode(self, mode):
        self.theme_mode = mode

    def sizeHint(self, option, index):
        # Folder cards should be rich and match the Note Grid aesthetic
        if option.widget:
            width = option.widget.viewport().width() - 20
            # If width is too large, we could do 2 columns, but for sidebar 1 is safer
            return QSize(int(width), 110)
        return QSize(250, 110)

    def paint(self, painter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        c = styles.ZEN_THEME.get(self.theme_mode, styles.ZEN_THEME["light"])
        is_selected = option.state & QStyle.StateFlag.State_Selected
        is_hover = option.state & QStyle.StateFlag.State_MouseOver
        
        # 1. Colors
        bg_color = QColor(c.get('card', "#FFFFFF"))
        text_color = QColor(c.get('foreground', "#3D3A38"))
        muted_color = QColor(c.get('muted_foreground', "#8D8682"))
        border_color = QColor(c.get('border', "#E0DDD9"))
        
        # 2. Check for Section Header (Type stored in UserRole + 2)
        item_type = index.data(Qt.ItemDataRole.UserRole + 2)
        if item_type == "SECTION_HEADER":
            rect = option.rect.adjusted(16, 10, -16, 0)
            painter.setPen(muted_color)
            font = QFont("Inter", 8, QFont.Weight.Bold)
            font.setStretch(100)
            painter.setFont(font)
            name = index.data(Qt.ItemDataRole.DisplayRole) or ""
            painter.drawText(rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, name.upper())
            painter.restore()
            return

        if is_selected:
            bg_color = QColor(c.get('selection_bg', c['secondary']))
            border_color = QColor(c.get('ring', c['primary']))
        elif is_hover:
            border_color = QColor(c.get('ring', c['primary']))
            
        # 3. Draw Card Rect
        rect = option.rect.adjusted(8, 6, -8, -6)
        path = QPainterPath()
        path.addRoundedRect(QRectF(rect), 12, 12)
        
        painter.setPen(QPen(border_color, 1))
        painter.setBrush(QBrush(bg_color))
        painter.drawPath(path)
        
        # 4. Data Extraction (DEFENSIVE)
        folder_color_raw = getattr(folder, 'color', None) if folder else None
        # Use theme foreground as default for better contrast
        default_icon_color = c.get('sidebar_fg', c.get('foreground', '#3D3A38'))
        folder_color_str = folder_color_raw if folder_color_raw else default_icon_color
        
        # 5. Layout: Left (Icon/Image) / Right (Content)
        img_width = 80
        content_margin = 12
        
        inner_rect = rect.adjusted(content_margin, content_margin, -content_margin, -content_margin)
        icon_rect = QRectF(inner_rect.x(), inner_rect.y(), img_width, inner_rect.height())
        
        # Draw Placeholder (Like notes)
        painter.save()
        placeholder_color = QColor(c.get('muted', "#F2F0ED"))
        p_path = QPainterPath()
        p_path.addRoundedRect(icon_rect, 8, 8)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(placeholder_color)
        painter.drawPath(p_path)
        
        # Determine Icon based on Folder Type/Name
        folder_name = index.data(Qt.ItemDataRole.DisplayRole) or ""
        icon_name = "folder"
        if "Trash" in folder_name: icon_name = "trash_2"
        elif "Archived" in folder_name: icon_name = "archive"
        elif "Recent" in folder_name: icon_name = "clock"
        elif "Ideas" in folder_name: icon_name = "heart"
        
        # Draw Icon
        icon_size = 40
        folder_icon = get_premium_icon(icon_name, color=folder_color_str)
        icon_pixmap = folder_icon.pixmap(icon_size, icon_size)
        icon_draw_rect = QRectF(
            icon_rect.center().x() - icon_size/2,
            icon_rect.center().y() - icon_size/2,
            icon_size, icon_size
        )
        painter.drawPixmap(icon_draw_rect.toRect(), icon_pixmap)
        painter.restore()
        
        # Text Area
        text_x = icon_rect.right() + 12
        text_width = inner_rect.right() - text_x
        text_rect = QRectF(text_x, inner_rect.y(), text_width, inner_rect.height())
        
        # 6. Draw Name
        name_text = folder_name if folder_name else "Untitled"
        painter.setPen(text_color)
        title_font = QFont("Inter", 10, QFont.Weight.Bold)
        title_font.setStretch(100)
        painter.setFont(title_font)
        
        elided_title = painter.fontMetrics().elidedText(name_text, Qt.TextElideMode.ElideRight, int(text_rect.width()))
        painter.drawText(text_rect.adjusted(0, 0, 0, -60), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, elided_title)
        
        # 7. Description (Small Muted Text)
        desc_text = getattr(folder, 'description', "") if folder else "Standard Folder"
        if "Trash" in folder_name: desc_text = "Deleted items shelf"
        elif "Archived" in folder_name: desc_text = "Hidden storage"
        elif "Recent" in folder_name: desc_text = "Continue where you left off"
        elif "Ideas" in folder_name: desc_text = "Pinned sparks & thoughts"
        
        desc_font = QFont("Inter", 8)
        painter.setFont(desc_font)
        painter.setPen(muted_color)
        desc_draw_rect = text_rect.adjusted(0, 22, 0, -25)
        elided_desc = painter.fontMetrics().elidedText(desc_text, Qt.TextElideMode.ElideRight, int(desc_draw_rect.width() * 2))
        painter.drawText(desc_draw_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap, elided_desc)
            
        # 8. Metadata (Bottom)
        meta_font = QFont("IBM Plex Mono", 7)
        painter.setFont(meta_font)
        painter.setPen(muted_color)
        
        created_at = getattr(folder, 'created_at', None) if folder else None
        meta_str = "Status: Active"
        if created_at:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(created_at)
                meta_str = "Created: " + dt.strftime("%b %d")
            except: pass
        if "Trash" in folder_name: meta_str = "System: Protected"
        elif "Recent" in folder_name: meta_str = "Auto-generated View"
        
        meta_r = QRectF(text_rect.x(), inner_rect.bottom() - 12, text_rect.width(), 12)
        painter.drawText(meta_r, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, meta_str)

        # Subtle Color Indicator dot
        dot_rect = QRectF(text_rect.x(), inner_rect.bottom() - 28, 8, 8)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(folder_color_str)))
        painter.drawEllipse(dot_rect)
        
        painter.setPen(muted_color)
        entity_name = "Notebook Entity" if folder else "System View"
        painter.drawText(dot_rect.adjusted(12, -4, 200, 10), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, entity_name)

        painter.restore()

class FolderListDelegate(QStyledItemDelegate):
    def __init__(self, parent=None, theme_mode="light"):
        super().__init__(parent)
        self.theme_mode = theme_mode

    def set_theme_mode(self, mode):
        self.theme_mode = mode

    def sizeHint(self, option, index):
        # Header or Standard Item?
        if index.data(Qt.ItemDataRole.UserRole + 2) == "SECTION_HEADER":
            return QSize(option.rect.width(), 40) # Headers more breathable
        return QSize(option.rect.width(), 48) # Premium item height

    def paint(self, painter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        c = styles.ZEN_THEME.get(self.theme_mode, styles.ZEN_THEME["light"])
        is_selected = option.state & QStyle.StateFlag.State_Selected
        is_hover = option.state & QStyle.StateFlag.State_MouseOver
        
        bg_color = QColor(c.get('card', "#FFFFFF"))
        text_color = QColor(c.get('foreground', "#3D3A38"))
        muted_color = QColor(c.get('muted_foreground', "#8D8682"))
        primary_color = QColor(c.get('primary', "#7B9E87"))
        
        rect = option.rect
        
        # 1. Determine Type
        item_type = index.data(Qt.ItemDataRole.UserRole + 2)
        
        if item_type == "SECTION_HEADER":
            # Just Draw Text
            header_text = index.data(Qt.ItemDataRole.DisplayRole) or ""
            painter.setPen(muted_color)
            font = QFont("Inter", 8, QFont.Weight.Bold)
            font.setStretch(100)
            painter.setFont(font)
            
            # Align bottom-left for headers
            text_rect = rect.adjusted(16, 8, -4, -4)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, header_text.upper())
            painter.restore()
            return
            
        elif item_type == "SPACER":
            # Draw nothing
            painter.restore()
            return

        # 2. Draw Background (Hover/Select) - No card bg by default!
        # In this "Clean List" mode, we only highlight on hover/select.
        
        if is_selected:
            # Subtle selection background
            sel_bg = QColor(c.get('selection_bg', c['secondary']))
            # sel_bg.setAlpha(150)
            painter.setBrush(QBrush(sel_bg))
            painter.setPen(Qt.PenStyle.NoPen)
            # Rounded pill shape for selection? Or full width?
            # User image shows highlighting. Let's do rounded pill with margins.
            # Change text color?
            sel_rect = rect.adjusted(4, 3, -4, -3)
            painter.drawRoundedRect(sel_rect, 10, 10)
            
            # Usually stays foreground in Zen, maybe Primary?
            # text_color = primary_color 
            
        elif is_hover:
            hover_bg = QColor(c.get('secondary', "#F5F5F4"))
            hover_bg.setAlpha(120)
            painter.setBrush(QBrush(hover_bg))
            painter.setPen(Qt.PenStyle.NoPen)
            sel_rect = rect.adjusted(4, 3, -4, -3)
            painter.drawRoundedRect(sel_rect, 10, 10)
            
        # 3. Icon
        icon = index.data(Qt.ItemDataRole.DecorationRole)
        icon_size = 18
        icon_x = rect.left() + 14
        
        if icon:
            # We want to use the QIcon but maybe recolor it if selected?
            # The icon passed in is already colored (premium icon).
            icon_rect = QRectF(icon_x, rect.center().y() - icon_size/2, icon_size, icon_size)
            icon.paint(painter, icon_rect.toRect(), Qt.AlignmentFlag.AlignCenter, QIcon.Mode.Normal, QIcon.State.On)
        
        # 4. Text
        text = index.data(Qt.ItemDataRole.DisplayRole)
        text_x = icon_x + icon_size + 12
        text_w = rect.width() - text_x - 40 # Reserve space for count
        
        if text:
            painter.setPen(text_color)
            font = QFont("Inter", 10) # Using 10pt/13px for cleaner look
            font.setStretch(100)
            if is_selected: font.setBold(True)
            painter.setFont(font)
            
            text_rect = QRectF(text_x, rect.top(), text_w, rect.height())
            elided = painter.fontMetrics().elidedText(text, Qt.TextElideMode.ElideRight, int(text_rect.width()))
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, elided)
            
        # 5. Badge (Right Aligned)
        # Check UserRole + 5 for Count Data
        count_data = index.data(Qt.ItemDataRole.UserRole + 5)
        if count_data:
            count_str = str(count_data)
            
            # Badge Rect
            badge_font = QFont("Inter", 8, QFont.Weight.Bold)
            painter.setFont(badge_font)
            fm = painter.fontMetrics()
            txt_w = fm.horizontalAdvance(count_str)
            pad_h = 8
            badge_w = max(20, txt_w + 12)
            badge_h = 16
            
            badge_x = rect.right() - badge_w - 12
            badge_y = rect.center().y() - badge_h/2
            badge_rect = QRectF(badge_x, badge_y, badge_w, badge_h)
            
            # Badge style
            is_active_badge = is_selected or "Ideas" in str(text) # Maybe highlight popular items?
            badge_bg = primary_color if is_active_badge else QColor(c.get('muted', "#F2F0ED"))
            badge_fg = QColor("#FFFFFF") if is_active_badge else muted_color
            
            painter.setBrush(QBrush(badge_bg))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(badge_rect, 8, 8)
            
            painter.setPen(badge_fg)
            painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, count_str)
            
        painter.restore()

class Sidebar(QWidget):
    folderSelected = pyqtSignal(str) # Emits folder ID
    createFolder = pyqtSignal(str, str) # folder_name, notebook_id
    deleteFolder = pyqtSignal(str)   # Emits folder ID
    renameFolder = pyqtSignal(str, str)  # Emits folder ID, new name
    exportFolder = pyqtSignal(str)   # Emits folder ID for export
    exportFolderWord = pyqtSignal(str) # NEW
    exportWhiteboard = pyqtSignal(str) # Emits folder ID for whiteboard export
    updateFolder = pyqtSignal(str, dict) # Emits folder ID, updates dict
    reorderFolder = pyqtSignal(str, int) # Emits folder ID, new position (index)
    requestHighlightPreview = pyqtSignal(str) # folder_id
    requestPdfPreview = pyqtSignal(str) # folder_id
    toggleTheme = pyqtSignal(str)  # Emits chosen theme key
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
        self.view_mode = VIEW_MODE_LIST
        self.current_icon_color = "#3D3A38" # Default for light

        self._setup_header()
        self._setup_search()
        self._setup_list()
        self._setup_bottom()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        width = self.width()
        
        # Adaptive Branding Refresh
        if hasattr(self, 'title_label'):
            # Zero out side margins in narrow state
            if width < 220:
                self.header_layout.setContentsMargins(0, 20, 0, 16)
            else:
                self.header_layout.setContentsMargins(16, 20, 16, 16)

            # Smoother Multi-Step Scaling
            if width > 280:
                font_size = 18
                text = "ZEN NOTES"
                spacing = 12
                show = True
            elif width > 240:
                font_size = 16
                text = "ZEN NOTES"
                spacing = 8
                show = True
            elif width > 200:
                font_size = 14
                text = "ZEN NOTES"
                spacing = 4
                show = True
            elif width > 160:
                font_size = 11
                text = "ZEN NOTES"
                spacing = 2
                show = True
            elif width > 130:
                font_size = 11
                text = "ZEN"
                spacing = 2
                show = True
            else:
                show = False

            if show:
                self.title_label.setText(text)
                self.title_label.setStyleSheet(f"font-size: {font_size}px; font-weight: bold; margin: 0px; padding: 0px;")
                if hasattr(self, 'brand_layout'): self.brand_layout.setSpacing(spacing)
                self.title_label.show()
            else:
                self.title_label.hide()

    def _setup_header(self):
        header_container = QWidget()
        header_container.setObjectName("SidebarHeader") # For Global Styling
        self.header_layout = QVBoxLayout(header_container)
        self.header_layout.setContentsMargins(16, 20, 16, 16) # More breathing room
        self.header_layout.setSpacing(16)
        
        # --- ROW 1: BRANDING ---
        brand_row = QWidget()
        self.brand_layout = QHBoxLayout(brand_row)
        self.brand_layout.setContentsMargins(0, 0, 0, 0)
        self.brand_layout.setSpacing(0) # Globally zero spacing for flush look
        
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
        
        self.brand_layout.addWidget(self.logo_container)
        
        # Title - constrain to text width so it doesn't absorb extra space
        self.title_label = QLabel("Zen Notes")
        self.title_label.setObjectName("SidebarTitle")
        self.title_label.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        self.brand_layout.addWidget(self.title_label)
        
        # Theme Toggle (Top Right)
        self.theme_btn = QPushButton() 
        self.theme_btn.setToolTip("Toggle Zen Mode")
        self.theme_btn.setFixedSize(24, 24)
        self.theme_btn.setIconSize(QSize(18, 18))
        self.theme_btn.setStyleSheet("QPushButton { border: none; background: transparent; padding: 0px; margin: 0px; border-radius: 4px; outline: none; } QPushButton:hover { background: rgba(0,0,0,0.05); }")
        self.theme_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_btn.clicked.connect(self._open_theme_chooser)
        self.brand_layout.addWidget(self.theme_btn)

        # Focus Mode Button
        self.focus_btn = QPushButton()
        self.focus_btn.setToolTip("Focus Mode")
        self.focus_btn.setFixedSize(24, 24)
        self.focus_btn.setIconSize(QSize(18, 18))
        self.focus_btn.setStyleSheet("QPushButton { border: none; background: transparent; padding: 0px; margin: 0px; border-radius: 4px; outline: none; } QPushButton:hover { background: rgba(0,0,0,0.05); }")
        self.focus_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.focus_btn.clicked.connect(self._open_focus_mode)
        self.brand_layout.addWidget(self.focus_btn)

        # Settings Button
        self.settings_btn = QPushButton()
        self.settings_btn.setToolTip("Settings")
        self.settings_btn.setFixedSize(24, 24)
        self.settings_btn.setIconSize(QSize(18, 18))
        self.settings_btn.setStyleSheet("QPushButton { border: none; background: transparent; padding: 0px; margin: 0px; border-radius: 4px; outline: none; } QPushButton:hover { background: rgba(0,0,0,0.05); }")
        self.settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.settings_btn.clicked.connect(lambda: pulse_button(self.settings_btn))
        self.brand_layout.addWidget(self.settings_btn)
        
        # Absorb remaining space AFTER icons (not between title and icons)
        self.brand_layout.addStretch()
        
        self.header_layout.addWidget(brand_row)
        
        # --- ROW 2: NOTEBOOK SELECTOR & CONTROLS ---
        nb_row = QWidget()
        nb_layout = QHBoxLayout(nb_row)
        nb_layout.setContentsMargins(0,0,0,0)
        nb_layout.setSpacing(8)
        
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

        # Vertical Controls (Small)
        controls_layout = QVBoxLayout()
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(0)
        
        # 1. Add Notebook
        self.add_folder_btn = QPushButton()
        self.add_folder_btn.setIcon(get_premium_icon("plus"))
        self.add_folder_btn.setFixedSize(24, 18)
        self.add_folder_btn.setIconSize(QSize(12, 12))
        self.add_folder_btn.setToolTip("New Notebook")
        self.add_folder_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_folder_btn.clicked.connect(lambda: (pulse_button(self.add_folder_btn), self.prompt_new_notebook()))
        # Style flat
        self.add_folder_btn.setStyleSheet("QPushButton { border: none; background: transparent; border-radius: 4px; } QPushButton:hover { background: rgba(0,0,0,0.1); }")
        
        # 2. Delete Notebook
        self.delete_nb_btn = QPushButton()
        self.delete_nb_btn.setIcon(get_premium_icon("trash")) 
        self.delete_nb_btn.setFixedSize(24, 18)
        self.delete_nb_btn.setIconSize(QSize(12, 12))
        self.delete_nb_btn.setToolTip("Delete Notebook")
        self.delete_nb_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.delete_nb_btn.clicked.connect(self._on_delete_notebook_clicked)
        self.delete_nb_btn.setStyleSheet("QPushButton { border: none; background: transparent; border-radius: 4px; } QPushButton:hover { background: rgba(239, 68, 68, 0.2); }")

        # 3. Lock
        self.lock_btn = QPushButton()
        self.lock_btn.setIcon(get_premium_icon("unlock"))
        self.lock_btn.setCheckable(True)
        self.lock_btn.setFixedSize(24, 18)
        self.lock_btn.setIconSize(QSize(12, 12))
        self.lock_btn.setToolTip("Lock Navigation")
        self.lock_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lock_btn.toggled.connect(self._on_lock_toggled)
        self.lock_btn.setStyleSheet("QPushButton { border: none; background: transparent; border-radius: 4px; } QPushButton:hover { background: rgba(0,0,0,0.1); }")

        controls_layout.addWidget(self.add_folder_btn)
        controls_layout.addWidget(self.delete_nb_btn)
        controls_layout.addWidget(self.lock_btn)
        
        nb_layout.addLayout(controls_layout)
        
        # --- End of Header --
        self.header_layout.addWidget(nb_row)
        self.layout.addWidget(header_container)

    def _setup_search(self):
        # Horizontal Layout: [ Search Bar ] [Sort] [Wrap] [Eye] [Mark]
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(16, 0, 16, 10) # Match header margin width, bottom spacing
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)


        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search folders...")
        self.search_bar.setFixedHeight(32)
        
        # Add Search Icon inside
        search_icon = get_premium_icon("search", color="#94A3B8")
        self.search_action = self.search_bar.addAction(search_icon, QLineEdit.ActionPosition.LeadingPosition)
        
        self.search_bar.setStyleSheet("""
            QLineEdit {
                border-radius: 8px;
                padding-left: 5px;
                padding-right: 10px;
                font-size: 11px;
                background: rgba(0,0,0,0.03);
                border: 1px solid rgba(0,0,0,0.05);
                color: #3D3A38;
            }
            QLineEdit:focus {
                background: #FFFFFF;
                border: 1px solid rgba(0,0,0,0.1);
            }
        """)
        self.search_bar.textChanged.connect(self.refresh_list)
        layout.addWidget(self.search_bar)

        # --- Action Buttons ---
        icon_size = 24
        
        # 1. Filter (replacing wrap)
        self.wrap_btn = QPushButton()
        self.wrap_btn.setIcon(get_premium_icon("filter"))
        self.wrap_btn.setToolTip("Filter Folders")
        self.wrap_btn.setFixedSize(icon_size, icon_size)
        self.wrap_btn.setIconSize(QSize(18, 18))
        self.wrap_btn.setCheckable(True)
        self.wrap_btn.clicked.connect(lambda: self.wrapToggled.emit(self.wrap_btn.isChecked()))
        self.wrap_btn.setStyleSheet("QPushButton { border: none; background: transparent; border-radius: 6px; } QPushButton:hover { background: rgba(0,0,0,0.05); } QPushButton:checked { background: rgba(0,0,0,0.1); }")
        layout.addWidget(self.wrap_btn)
        
        # 2. Preview
        self.preview_btn = QPushButton()
        self.preview_btn.setIcon(get_premium_icon("eye"))
        self.preview_btn.setToolTip("Preview PDF")
        self.preview_btn.setFixedSize(icon_size, icon_size)
        self.preview_btn.setIconSize(QSize(16, 16))
        self.preview_btn.clicked.connect(lambda: self.requestPdfPreview.emit(str(self._get_active_folder_id()))) 
        self.preview_btn.setStyleSheet("QPushButton { border: none; background: transparent; border-radius: 4px; } QPushButton:hover { background: rgba(0,0,0,0.1); }")
        layout.addWidget(self.preview_btn)

        # 3. Highlight
        self.highlight_preview_btn = QPushButton()
        self.highlight_preview_btn.setIcon(get_premium_icon("sparkle"))
        self.highlight_preview_btn.setToolTip("Highlights")
        self.highlight_preview_btn.setFixedSize(icon_size, icon_size)
        self.highlight_preview_btn.setIconSize(QSize(16, 16))
        self.highlight_preview_btn.clicked.connect(lambda: self.requestHighlightPreview.emit(str(self._get_active_folder_id())))
        self.highlight_preview_btn.setStyleSheet("QPushButton { border: none; background: transparent; border-radius: 4px; } QPushButton:hover { background: rgba(0,0,0,0.1); }")
        layout.addWidget(self.highlight_preview_btn)

        self.layout.addWidget(container)

    def _get_active_folder_id(self):
        """Helper to get currently selected folder ID regardless of view mode."""
        item = self.list_widget.currentItem()
        if not item: return ""
        
        if isinstance(item, QTreeWidgetItem):
            data = item.data(0, Qt.ItemDataRole.UserRole)
        else:
            data = item.data(Qt.ItemDataRole.UserRole)
            
        return data if isinstance(data, str) else ""

    def _setup_list(self):
        self.stacked_list = QStackedWidget()
        
        # 1. Tree View (List Mode)
        self.list_tree = QTreeWidget()
        self.list_tree.setObjectName("FolderTree")
        self.list_tree.setHeaderHidden(True)
        self.list_tree.setIndentation(20)
        self.list_tree.setAnimated(True)
        self.list_tree.setRootIsDecorated(True)
        self.list_tree.setUniformRowHeights(True)
        self.list_tree.itemClicked.connect(self.on_item_clicked)
        self.list_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_tree.customContextMenuRequested.connect(self.show_context_menu)
        
        self.list_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_tree.customContextMenuRequested.connect(self.show_context_menu)
        
        self.list_delegate = FolderListDelegate(self.list_tree, self.theme_mode)
        self.list_tree.setItemDelegate(self.list_delegate)
        
        # 2. List View (Grid Mode)
        self.list_grid = QListWidget()
        self.list_grid.setObjectName("FolderGrid")
        self.list_grid.setViewMode(QListWidget.ViewMode.IconMode)
        self.list_grid.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.list_grid.setMovement(QListWidget.Movement.Static)
        self.list_grid.setSpacing(8)
        self.list_grid.setWordWrap(True)
        self.list_grid_delegate = FolderCardDelegate(self.list_grid, self.theme_mode)
        self.list_grid.setItemDelegate(self.list_grid_delegate)
        self.list_grid.itemClicked.connect(self._on_grid_item_clicked)
        self.list_grid.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_grid.customContextMenuRequested.connect(self.show_context_menu)
        
        self.stacked_list.addWidget(self.list_tree)
        self.stacked_list.addWidget(self.list_grid)
        
        self.layout.addWidget(self.stacked_list)
        
        # Active reference
        self.list_widget = self.list_tree

    def _on_grid_item_clicked(self, item):
        # Fake tree-like event for grid items
        self.on_item_clicked(item, 0)


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

    def _open_focus_mode(self):
        """Open the Focus Mode dialog."""
        pulse_button(self.focus_btn)
        current = getattr(self, 'theme_mode', 'light')
        dm = None
        if hasattr(self, 'window') and hasattr(self.window(), 'data_manager'):
            dm = self.window().data_manager
        dlg = FocusModeDialog(current_theme=current, data_manager=dm, parent=self.window())
        dlg.exec()

    def _open_theme_chooser(self):
        """Open the visual theme chooser dialog."""
        pulse_button(self.theme_btn)
        current = getattr(self, 'theme_mode', 'light')
        dlg = ThemeChooserDialog(current_theme=current, parent=self.window())
        dlg.themeChosen.connect(lambda key: self.toggleTheme.emit(key))
        dlg.exec()

    def set_theme_mode(self, mode):
        """Updates the sidebar header and components for the given theme mode."""
        self.theme_mode = mode
        c = styles.ZEN_THEME.get(mode, styles.ZEN_THEME["light"])
        # DYNAMIC COLOR lookup instead of binary check
        self.current_icon_color = c.get('sidebar_fg', c.get('foreground', '#000000'))
        icon_color = self.current_icon_color
        
        # Update Delegates
        if hasattr(self, 'list_delegate'):
            self.list_delegate.set_theme_mode(mode)
        if hasattr(self, 'list_grid_delegate'):
            self.list_grid_delegate.set_theme_mode(mode)
            
        # Update Header Icons
        is_dark_theme = mode in ("dark", "dark_blue", "ocean_depth", "noir_ember")
        self.theme_btn.setIcon(get_premium_icon("sun" if is_dark_theme else "moon", color=icon_color))
        self.focus_btn.setIcon(get_premium_icon("headphones", color=icon_color))
        self.settings_btn.setIcon(get_premium_icon("settings", color=icon_color))
        
        # Update Bottom Icons
        self.panel_toggle_btn.setIcon(get_premium_icon("panel_toggle", color=icon_color))
        
        # Update View Toggle Icon
        if self.view_mode == VIEW_MODE_GRID:
            self.view_toggle_btn.setIcon(get_premium_icon("layout_list", color=icon_color))
        else:
            self.view_toggle_btn.setIcon(get_premium_icon("layout_grid", color=icon_color))
            
        # Selectors & Input
        self.nb_selector.setStyleSheet(f"QComboBox {{ background: {c.get('input', '#FFFFFF')}; color: {c['foreground']}; border: 1px solid {c.get('border', '#E0DDD9')}; border-radius: 6px; padding: 4px; }}")
        # FIXED: Preserve compact search bar sizing (32px height, 8px radius, 11px font)
        search_icon_color = c.get('muted_foreground', '#94A3B8')
        if hasattr(self, 'search_action'):
            self.search_action.setIcon(get_premium_icon("search", color=search_icon_color))
        
        # Detect ALL dark themes properly
        is_dark = mode in ("dark", "dark_blue", "ocean_depth", "noir_ember")
            
        self.search_bar.setStyleSheet(f"""
            QLineEdit {{
                background: {c.get('input', '#1E1E1E') if is_dark else 'rgba(0,0,0,0.03)'};
                color: {c['foreground']};
                border: 1px solid {c.get('border', '#333') if is_dark else 'rgba(0,0,0,0.05)'};
                border-radius: 8px;
                padding-left: 5px; padding-right: 10px;
                font-size: 11px;
            }}
            QLineEdit:focus {{
                background: {c.get('background', '#FFFFFF')};
                border: 1px solid {c.get('primary', '#7B9E87')};
            }}
        """)
        self.search_bar.setFixedHeight(32)
        
        # Action Buttons styling (Search Row) — preserve 20px size
        btn_style = f"QPushButton {{ border: none; background: transparent; border-radius: 4px; }} QPushButton:hover {{ background: {c.get('secondary', 'rgba(0,0,0,0.1)')}; }} QPushButton:checked {{ background: {c.get('primary', 'rgba(0,0,0,0.15)')}; }}"

        for btn in [self.wrap_btn, self.preview_btn, self.highlight_preview_btn]:
            btn.setStyleSheet(btn_style)
            btn.setFixedSize(24, 24)
            btn.setIconSize(QSize(18, 18))
        
        # Refresh Icons in Search Row
        self.wrap_btn.setIcon(get_premium_icon("filter", color=icon_color))
        self.preview_btn.setIcon(get_premium_icon("eye", color=icon_color))
        self.highlight_preview_btn.setIcon(get_premium_icon("sparkle", color=icon_color))
        
        # Refresh to apply theme to icons in list
        self.refresh_list()
        
        # Action Icons
        # Note: Primary/Destructive buttons typically have contrasting text (white/white)
        # UPDATE: Now they are flat icons next to title, so use theme icon_color
        self.add_folder_btn.setIcon(get_premium_icon("plus", color=icon_color))
        self.delete_nb_btn.setIcon(get_premium_icon("trash", color=icon_color))
        
        # Lock button (Normal: Icon Color, Checked: White)
        lock_color = "white" if self.lock_btn.isChecked() else icon_color
        self.lock_btn.setIcon(get_premium_icon("lock" if self.lock_btn.isChecked() else "unlock", color=lock_color))
        
        # 3. Update Stylesheets for Hover Visibility
        hover_bg = "rgba(255,255,255,0.1)" if is_dark else "rgba(0,0,0,0.1)"
        checked_bg = "rgba(255,255,255,0.15)" if is_dark else "rgba(0,0,0,0.15)"

        
        flat_style = f"QPushButton {{ border: none; background: transparent; border-radius: 4px; }} QPushButton:hover {{ background: {hover_bg}; }}"
        checkable_style = f"QPushButton {{ border: none; background: transparent; border-radius: 4px; }} QPushButton:hover {{ background: {hover_bg}; }} QPushButton:checked {{ background: {checked_bg}; }}"
        delete_style = f"QPushButton {{ border: none; background: transparent; border-radius: 4px; }} QPushButton:hover {{ background: rgba(239, 68, 68, 0.2); }}"

        # Apply to Vertical Controls
        self.add_folder_btn.setStyleSheet(flat_style)
        self.delete_nb_btn.setStyleSheet(delete_style)
        self.lock_btn.setStyleSheet(checkable_style)
        
        # Apply to Horizontal Controls
        self.wrap_btn.setStyleSheet(checkable_style)
        self.preview_btn.setStyleSheet(flat_style)
        self.highlight_preview_btn.setStyleSheet(flat_style)
        
        # Apply to Bottom Controls
        self.panel_toggle_btn.setStyleSheet(flat_style)
        self.view_toggle_btn.setStyleSheet(flat_style)
        
        # Update Bottom Icons
        view_icon = "layout_grid" if self.view_mode == VIEW_MODE_LIST else "layout_list"
        self.view_toggle_btn.setIcon(get_premium_icon(view_icon, color=icon_color))
        self.panel_toggle_btn.setIcon(get_premium_icon("panel_toggle", color=icon_color))
        
        # Add Button Icon (Usually white for Primary)
        self.add_btn.setIcon(get_premium_icon("plus", color="#FFFFFF"))
        
        # Final refresh to apply everything
        self.refresh_list()


    def _on_delete_notebook_clicked(self):
        nb_id = self.nb_selector.currentData()
        if nb_id:
            self.confirm_delete_notebook(nb_id)

    def _setup_bottom(self):
        bottom_container = QWidget()
        # Main layout for bottom - vertical to stack rows if needed
        bottom_main_layout = QVBoxLayout(bottom_container)
        bottom_main_layout.setContentsMargins(10, 10, 10, 15)
        bottom_main_layout.setSpacing(10)

        # Control Row (Panel Toggle, Grid Toggle, New Button)
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(8)

        # 1. Panel Toggle
        self.panel_toggle_btn = QPushButton()
        self.panel_toggle_btn.setObjectName("ViewToggleBtn") # Shared premium style
        self.panel_toggle_btn.setFixedSize(36, 36)
        self.panel_toggle_btn.setIconSize(QSize(20, 20))
        self.panel_toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.panel_toggle_btn.clicked.connect(self.panelToggleRequest.emit)
        controls_layout.addWidget(self.panel_toggle_btn)

        # 2. View Mode Toggle
        self.view_toggle_btn = QPushButton()
        self.view_toggle_btn.setObjectName("ViewToggleBtn")
        self.view_toggle_btn.setFixedSize(36, 36)
        self.view_toggle_btn.setIconSize(QSize(20, 20))
        self.view_toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.view_toggle_btn.clicked.connect(self.toggle_view_mode)
        controls_layout.addWidget(self.view_toggle_btn)

        # 3. New Folder Button (Now integrated into the row)
        self.add_btn = QPushButton(" New Folder")
        self.add_btn.setIcon(get_premium_icon("plus", color="white"))
        self.add_btn.setObjectName("NewFolderBtn") # Shared NewNoteBtn style essentially
        self.add_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.add_btn.clicked.connect(lambda: (pulse_button(self.add_btn), self.prompt_new_folder()))
        controls_layout.addWidget(self.add_btn)

        bottom_main_layout.addLayout(controls_layout)
        self.layout.addWidget(bottom_container)

    def toggle_view_mode(self):
        """Toggle between List and Grid view for folders."""
        new_mode = VIEW_MODE_GRID if self.view_mode == VIEW_MODE_LIST else VIEW_MODE_LIST
        self.set_view_mode(new_mode)

    def set_view_mode(self, mode):
        """Standardize view mode and update UI."""
        if self.view_mode == mode: return
        self.view_mode = mode
        
        # Use theme-aware color for icons
        icon_color = "#FFFFFF" if self.theme_mode in ("dark", "dark_blue", "ocean_depth", "noir_ember") else "#09090b"
        
        if mode == VIEW_MODE_GRID:
            # Switch to Grid Widget
            self.stacked_list.setCurrentWidget(self.list_grid)
            self.list_widget = self.list_grid
            self.view_toggle_btn.setIcon(get_premium_icon("layout_list", color=icon_color))
            self.view_toggle_btn.setToolTip("Switch to List View")
        else:
            # Switch to Tree Widget
            self.stacked_list.setCurrentWidget(self.list_tree)
            self.list_widget = self.list_tree
            self.view_toggle_btn.setIcon(get_premium_icon("layout_grid", color=icon_color))
            self.view_toggle_btn.setToolTip("Switch to Grid View")
        
        # Refresh current view
        self.refresh_list()

    def set_wrap_mode(self, enabled):
        self.wrap_btn.setChecked(enabled)
        self.list_widget.setWordWrap(enabled)
        # Force a viewport update to trigger sizeHint recalculation
        self.list_widget.viewport().update()
        self.refresh_list()

    def toggle_sort(self):
        self.sort_descending = not self.sort_descending
        self.refresh_list()

    def load_folders(self, folders):
        self.all_folders = folders
        self.refresh_list()
        
    def refresh_list(self):
        search_text = self.search_bar.text().lower()
        self.list_tree.clear()
        self.list_grid.clear()
        
        is_dark = self.theme_mode in ["dark", "dark_blue", "ocean_depth", "noir_ember"]

        # --- DATA PREPARATION ---
        selected_nb_id = self.nb_selector.currentData()
        nb = next((n for n in self.all_notebooks if n.id == selected_nb_id), None)
        nb_folder_ids = nb.folder_ids if nb else []
        
        active_folders = []
        archived_folders = []
        ideas_folder = None
        
        for f in self.all_folders:
            if f.name == "Ideas & Sparks" and f.id in nb_folder_ids:
                ideas_folder = f
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

        # Build Lists for the Grid View too (Flat representation for Grid)
        all_display_folders = []
        if ideas_folder: all_display_folders.append(ideas_folder)
        all_display_folders.extend(active_folders)
        # Not showing Archived in Grid for now to keep it clean, or we can add them at bottom.

        # --- UI BUILDING ---
        
        # Prepare Unified Display List (Favorites -> Active -> System)
        all_display_items = []
        
        # 1. Favorites
        all_display_items.append(("Favorites", "FAVORITES", "HEADER"))
        if ideas_folder: all_display_items.append(("Ideas & Sparks", ideas_folder, "FAVORITES"))
        fav_folders = [f for f in active_folders if f.is_pinned]
        for f in fav_folders:
            all_display_items.append((f.name, f, "FAVORITES"))
            
        # 2. Recent (Special)
        all_display_items.append(("Recent", "RECENT_ROOT", "RECENT"))
        
        # 3. Active
        all_display_items.append(("", "", "SPACER"))
        all_display_items.append(("Folders", "FOLDERS", "HEADER"))
        for i, f in enumerate(active_folders, 1):
            all_display_items.append((f.name, f, "FOLDERS", i))
            
        # 4. System
        all_display_items.append(("", "", "SPACER"))
        all_display_items.append(("System", "SYSTEM", "HEADER"))
        all_display_items.append(("Trash", "TRASH_ROOT", "SYSTEM"))
        if archived_folders:
            all_display_items.append((f"Archived ({len(archived_folders)})", "ARCHIVED_ROOT", "SYSTEM"))

        if self.view_mode == VIEW_MODE_GRID:
            # GRID VIEW POPULATION
            for name, data, section, *idx in all_display_items:
                if name == "": continue # Skip spacers
                
                item = QListWidgetItem(name)
                
                # Check for count data provided in a tuple like ("Ideas & Sparks", folder, "FAVORITES", count)
                # Helper to extract count if present in *idx
                count_val = idx[1] if len(idx) > 1 else None # enumerated index is idx[0]
                
                # ... Grid doesn't use badges heavily, but we can standard logic
                
                # Set icon based on section or object
                i_color = getattr(data, 'color', "#7B9E87") if not isinstance(data, str) else None
                item.setIcon(get_premium_icon("folder", color=i_color))
                
                is_heading = data in ["FAVORITES", "FOLDERS", "SYSTEM"]
                if is_heading:
                    item.setData(Qt.ItemDataRole.UserRole + 2, "SECTION_HEADER")
                    item.setSizeHint(QSize(0, 40))
                
                if isinstance(data, str): # Roots or Headings
                    item.setData(Qt.ItemDataRole.UserRole, data)
                else: # Folder Object
                    item.setData(Qt.ItemDataRole.UserRole, data.id)
                    item.setData(Qt.ItemDataRole.UserRole + 1, data)
                
                self.list_grid.addItem(item)
            return # Exit early after grid population

        # LIST VIEW (TREE) POPULATION (New Clean Style)
        # Use addTopLevelItem directly with data roles for the delegate
        
        # 1. Favorites
        self._add_list_node("FAVORITES", is_header=True)
        if ideas_folder:
            # Get count of ideas? For now use a dummy or calculated if available
            # Note count not readily available on folder obj unless calculated
            # Assuming Ideas count is meaningful. 
            # In user request image: "Ideas & Sparks   4"
            # Let's fake it or look it up if possible. For now, pass None or hardcode if we knew.
            # Using '4' as placeholder? No, better not to show WRONG data.
            # If we have note_count on folder:
            note_count = getattr(ideas_folder, 'note_count', None) 
            self._add_list_node("Ideas & Sparks", ideas_folder, icon="heart", icon_color="#f472b6", count=note_count)
            
        for f in fav_folders:
            self._add_list_node(f.name, f, count=getattr(f, 'note_count', None))

        # 2. Recent
        # Use semantic blue that adapts to theme luminance
        recent_color = "#60A5FA" if is_dark else "#3b82f6"
        self._add_list_node("Recent", "RECENT_ROOT", icon="clock", icon_color=recent_color)

        # 3. Folders
        self._add_list_node("", is_spacer=True)
        self._add_list_node("FOLDERS", is_header=True)
        for i, f in enumerate(active_folders, 1):
            self._add_list_node(f.name, f, index_prefix=f"{i}. ", count=getattr(f, 'note_count', None))
            
        # 4. System
        self._add_list_node("", is_spacer=True)
        self._add_list_node("SYSTEM", is_header=True)
        trash_color = "#9CA3AF" if is_dark else "#64748b"
        self._add_list_node("Trash", "TRASH_ROOT", icon="trash_2", icon_color=trash_color)
        
        if archived_folders:
            arch_count = len(archived_folders)
            # Pass count explicitly
            self._add_list_node("Archived", "ARCHIVED_ROOT", icon="archive", icon_color="#F59E0B", count=arch_count)


    def _add_list_node(self, text, data=None, is_header=False, is_spacer=False, icon="folder", icon_color=None, count=None, index_prefix=""):
        item = QTreeWidgetItem([text])
        
        if is_spacer:
            item.setData(0, Qt.ItemDataRole.UserRole + 2, "SPACER")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.list_tree.addTopLevelItem(item)
            return

        if is_header:
            item.setData(0, Qt.ItemDataRole.UserRole + 2, "SECTION_HEADER")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.list_tree.addTopLevelItem(item)
            return

        # Prepare Icon
        if isinstance(data, str): # Root ID
            item.setData(0, Qt.ItemDataRole.UserRole, data)
            final_icon = icon
            final_color = icon_color or self.current_icon_color
        else: # Folder Object
            item.setData(0, Qt.ItemDataRole.UserRole, data.id)
            item.setData(0, Qt.ItemDataRole.UserRole + 1, data)
            final_icon = icon
            final_color = getattr(data, 'color', self.current_icon_color) if not icon_color else icon_color
        
        item.setIcon(0, get_premium_icon(final_icon, color=final_color))
        
        # Display Text
        display_text = f"{index_prefix}{text}"
        item.setText(0, display_text)
        
        # Count Badge
        if count is not None:
            item.setData(0, Qt.ItemDataRole.UserRole + 5, count) # Badge Data
            
        self.list_tree.addTopLevelItem(item)

    def _add_header_item(self, text):
        # Legacy: Kept if anything else calls it, but mostly replaced by _add_list_node
        self._add_list_node(text, is_header=True)
        
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
        
        icon_color = "white" if self.theme_mode in ("dark", "dark_blue", "ocean_depth", "noir_ember") else None
        item.setIcon(0, get_combined_indicators(indicators, color=icon_color))
        return item

    def on_item_clicked(self, item, column):
        if isinstance(item, QTreeWidgetItem):
            data = item.data(0, Qt.ItemDataRole.UserRole)
        else:
            data = item.data(Qt.ItemDataRole.UserRole)
            
        if not data: return
        
        if isinstance(data, str) and data.startswith("NOTEBOOK:"):
            nb_id = data.split(":")[1]
            idx = self.nb_selector.findData(nb_id)
            if idx >= 0:
                self.nb_selector.setCurrentIndex(idx)
            return
            
        if data == "ARCHIVED_ROOT":
            if isinstance(item, QTreeWidgetItem):
                item.setExpanded(not item.isExpanded())
            return
            
        # Emit folder selection
        self.folderSelected.emit(str(data))

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
        msg = f"This will <b style='color: #ef4444;'>PERMANENTLY DELETE</b> all folders and notes in notebook <b style='color: #ef4444;'>'{name_to_type}'</b>.<br><br>This action <b style='color: #ef4444;'>cannot be undone from the Trash</b>.<br><br>Please type the name of the notebook to confirm:"
        
        typed_name, ok = ZenInputDialog.getText(self, "Confirm Notebook Deletion", msg)
        
        if ok:
            if typed_name.strip() == name_to_type:
                self.deleteNotebook.emit(nb_id)
            else:
                QMessageBox.warning(self, "Incorrect Name", "The name entered did not match. Deletion cancelled.")

    def confirm_delete_folder(self, folder_id):
        folder = next((f for f in self.all_folders if f.id == folder_id), None)
        if not folder: return
        
        if QMessageBox.question(self, "Move to Trash", f"Move folder '{folder.name}' to Trash? All notes inside will be moved as well.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self.deleteFolder.emit(folder_id)

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

        # Determine the correct data based on item type (fix TypeError)
        if isinstance(item, QTreeWidgetItem):
            data = item.data(0, Qt.ItemDataRole.UserRole)
            display_name = item.text(0)
        else:
            data = item.data(Qt.ItemDataRole.UserRole)
            display_name = item.text()

        menu = QMenu()
        menu.setStyleSheet("QMenu { menu-scrollable: 1; }")
        
        active_widget = self.list_widget # Usually Tree or List

        if isinstance(data, str) and data.startswith("NOTEBOOK:"):
            nb_id = data.split(":")[1]
            add_action = menu.addAction(get_premium_icon("folder_add"), "Add Folder Here")
            rename_action = menu.addAction(get_premium_icon("edit"), "Rename Notebook")
            delete_action = menu.addAction(get_premium_icon("delete"), "Delete Notebook")
            
            action = menu.exec(active_widget.mapToGlobal(pos))
            if action == add_action:
                self.prompt_new_folder(nb_id)
            elif action == rename_action:
                self.prompt_rename_notebook(nb_id, display_name)
            elif action == delete_action:
                self.confirm_delete_notebook(nb_id)
            return

        # Folder Context Menu (Standard)
        if data in ["ALL_NOTEBOOKS_ROOT", "ARCHIVED_ROOT", "RECENT_ROOT", "TRASH_ROOT"]: # Added RECENT_ROOT, TRASH_ROOT
            return

        folder_id = data
        folder = next((f for f in self.all_folders if f.id == folder_id), None)
        if not folder: return

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
        export_word_act = menu.addAction(get_premium_icon("doc"), "Export Folder to Word") # NEW
        
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
        elif action == export_word_act: # NEW
            self.exportFolderWord.emit(folder_id)
        elif action == delete_act:
            self.confirm_delete_folder(folder_id)
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
