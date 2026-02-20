import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, 
    QLineEdit, QPushButton, QHBoxLayout, QMenu, QMessageBox, QFileDialog,
    QFrame, QLabel, QComboBox, QSizePolicy, QColorDialog, QStackedWidget,
    QListWidget, QListWidgetItem, QStyledItemDelegate, QStyle
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QRect, QRectF
from PyQt6.QtGui import QFont, QColor, QAction, QPainter, QIcon, QBrush, QPen, QPainterPath, QLinearGradient, QPixmap
import ui.styles as styles
from util.icon_factory import get_premium_icon, get_combined_indicators
from ui.zen_dialog import ZenInputDialog
from ui.theme_chooser import ThemeChooserDialog
from ui.focus_mode import FocusModeDialog
from ui.animations import pulse_button
from models.folder import Folder

VIEW_MODE_LIST = "list"
VIEW_MODE_GRID = "grid"

class FolderCardDelegate(QStyledItemDelegate):
    def __init__(self, parent=None, theme_mode="light"):
        super().__init__(parent)
        self.theme_mode = theme_mode
        self.cover_cache = {} # path -> QPixmap

    def set_theme_mode(self, mode):
        self.theme_mode = mode

    def sizeHint(self, option, index):
        # Match NoteCardDelegate responsive aesthetic
        if option.widget:
            viewport = option.widget.viewport()
            total_width = viewport.width()
            
            # Margins (Standardized for Zen aesthetic)
            margin = 16 
            available_width = total_width - margin
            
            # Clamp width but keep it responsive
            card_width = min(420, max(200, available_width))
            
            return QSize(int(card_width), 110)
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
        folder = index.data(Qt.ItemDataRole.UserRole + 1)
        folder_color_raw = getattr(folder, 'color', None) if folder else None
        # Use theme foreground as default for better contrast
        default_icon_color = c.get('sidebar_fg', c.get('foreground', '#3D3A38'))
        folder_color_str = folder_color_raw if folder_color_raw else default_icon_color
        
        # Determine Icon properties early to avoid NameError
        folder_name = index.data(Qt.ItemDataRole.DisplayRole) or ""
        icon_name = "folder"
        if "Trash" in folder_name: icon_name = "trash_2"
        elif "Archived" in folder_name: icon_name = "archive"
        elif "Recent" in folder_name: icon_name = "clock"
        elif "Ideas" in folder_name: icon_name = "heart"
        icon_size = 40
        
        # 5. Layout: Left (Icon/Image) / Right (Content)
        img_width = 80
        content_margin = 12
        
        inner_rect = rect.adjusted(content_margin, content_margin, -content_margin, -content_margin)
        icon_rect = QRectF(inner_rect.x(), inner_rect.y(), img_width, inner_rect.height())
        
        # 5. Draw Image or Placeholder
        has_image = False
        if getattr(folder, 'cover_image', None) and os.path.exists(folder.cover_image):
            pixmap = self.cover_cache.get(folder.cover_image)
            if not pixmap:
                pixmap = QPixmap(folder.cover_image)
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(QSize(200, 200), 
                                         Qt.AspectRatioMode.KeepAspectRatioByExpanding, 
                                         Qt.TransformationMode.SmoothTransformation)
                    self.cover_cache[folder.cover_image] = pixmap
            
            if pixmap and not pixmap.isNull():
                has_image = True
                painter.save()
                
                # Aspect Fill logic for Folder Icon
                target_rect = icon_rect
                target_ratio = target_rect.width() / target_rect.height() if target_rect.height() > 0 else 1
                source_ratio = pixmap.width() / pixmap.height() if pixmap.height() > 0 else 1
                
                source_rect = QRectF(pixmap.rect())
                if source_ratio > target_ratio:
                    new_width = source_rect.height() * target_ratio
                    x_offset = (source_rect.width() - new_width) / 2
                    source_rect = QRectF(x_offset, 0, new_width, source_rect.height())
                else:
                    new_height = source_rect.width() / target_ratio
                    y_offset = (source_rect.height() - new_height) / 2
                    source_rect = QRectF(0, y_offset, source_rect.width(), new_height)
                
                # Rounded clip
                img_path = QPainterPath()
                img_path.addRoundedRect(target_rect, 8, 8) # Inner radius
                painter.setClipPath(img_path)
                painter.drawPixmap(target_rect, pixmap, source_rect)
                painter.restore()

        if not has_image:
            # Draw Placeholder (Like notes)
            painter.save()
            placeholder_color = QColor(c.get('muted', "#F2F0ED"))
            p_path = QPainterPath()
            p_path.addRoundedRect(icon_rect, 8, 8)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(placeholder_color)
            painter.drawPath(p_path)
            
            # Draw Icon
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
        item_type = index.data(Qt.ItemDataRole.UserRole + 2)
        if item_type == "SECTION_HEADER":
            return QSize(option.rect.width(), 28)
        if item_type == "SPACER":
            return QSize(option.rect.width(), 6)
        return QSize(option.rect.width(), 36)

    def paint(self, painter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        c = styles.ZEN_THEME.get(self.theme_mode, styles.ZEN_THEME["light"])
        is_dark = self.theme_mode in ("dark", "dark_blue", "ocean_depth", "noir_ember")
        is_selected = option.state & QStyle.StateFlag.State_Selected
        is_hover = option.state & QStyle.StateFlag.State_MouseOver
        
        text_color = QColor(c.get('foreground', "#3D3A38"))
        muted_color = QColor(c.get('muted_foreground', "#8D8682"))
        primary_color = QColor(c.get('primary', "#7B9E87"))
        
        rect = option.rect
        item_type = index.data(Qt.ItemDataRole.UserRole + 2)
        
        # ── SECTION HEADER ──
        if item_type == "SECTION_HEADER":
            header_text = index.data(Qt.ItemDataRole.DisplayRole) or ""
            
            # Check for Minimized State
            if rect.width() < 80:
                # Draw Icon Centered
                icon_name = "folder"
                if "Favorites" in header_text: icon_name = "heart"
                elif "Recent" in header_text: icon_name = "clock"
                elif "Trash" in header_text: icon_name = "trash_2"
                elif "Notebooks" in header_text: icon_name = "book"
                
                # Use muted, slightly transparent color
                icon_color = QColor(c.get('muted_foreground', '#8D8682'))
                icon = get_premium_icon(icon_name, color=icon_color.name())
                
                icon_size = 20
                icon_rect = QRectF(
                    rect.center().x() - icon_size/2,
                    rect.center().y() - icon_size/2,
                    icon_size, icon_size
                )
                painter.drawPixmap(icon_rect.toRect(), icon.pixmap(icon_size, icon_size))
                painter.restore()
                return

            # JetBrains Mono, 9px, weight 500, letter-spacing 0.16em
            font = QFont("JetBrains Mono", 7)
            font.setWeight(QFont.Weight.Medium)
            font.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 116)
            painter.setFont(font)
            
            # Check for toggle (Chevron)
            section_key = index.data(Qt.ItemDataRole.UserRole + 3)
            # Fetch explicitly as bool/int because sometimes it might be None if not set
            is_expanded_val = index.data(Qt.ItemDataRole.UserRole + 4)
            is_expanded = bool(is_expanded_val) if is_expanded_val is not None else True
            
            # Use muted color matching --text-muted
            label_color = QColor(c.get('muted_foreground', '#4d5370'))
            label_color.setAlpha(160)

            if section_key:
                # Draw Chevron
                painter.save()
                arrow_size = 8
                # Center vertically based on text baseline approx or rect center
                arrow_y = rect.center().y() - arrow_size / 2
                arrow_rect = QRectF(rect.left() + 8, arrow_y, arrow_size, arrow_size)
                
                path = QPainterPath()
                if is_expanded:
                    # Down Arrow
                    path.moveTo(arrow_rect.left(), arrow_rect.top() + 3)
                    path.lineTo(arrow_rect.center().x(), arrow_rect.bottom() - 3)
                    path.lineTo(arrow_rect.right(), arrow_rect.top() + 3)
                else:
                    # Right Arrow
                    path.moveTo(arrow_rect.left() + 2, arrow_rect.top())
                    path.lineTo(arrow_rect.right() - 2, arrow_rect.center().y())
                    path.lineTo(arrow_rect.left() + 2, arrow_rect.bottom())
                
                painter.setPen(QPen(label_color, 1.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawPath(path)
                painter.restore()
            
            # Draw label text
            label_text = header_text.upper()
            fm = painter.fontMetrics()
            text_w = fm.horizontalAdvance(label_text)
            
            text_left = rect.left() + 20
            text_rect = QRectF(text_left, rect.top(), text_w + 4, rect.height())
            # Use muted color matching --text-muted
            label_color = QColor(c.get('muted_foreground', '#4d5370'))
            label_color.setAlpha(160)
            painter.setPen(label_color)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom, label_text)
            
            # Trailing gradient line (like ::after in zen-notes.html)
            line_x_start = text_left + text_w + 10
            line_x_end = rect.right() - 20
            if line_x_end > line_x_start:
                line_y = int(rect.bottom() - fm.descent() - fm.height() / 2 + 2)
                gradient = QLinearGradient(line_x_start, line_y, line_x_end, line_y)
                line_base = QColor(c.get('border', '#E0DDD9'))
                line_base.setAlpha(30 if is_dark else 50)
                gradient.setColorAt(0, line_base)
                gradient.setColorAt(1, QColor(0, 0, 0, 0))
                painter.setPen(QPen(QBrush(gradient), 1))
                painter.drawLine(int(line_x_start), line_y, int(line_x_end), line_y)
            
            painter.restore()
            return
            
        elif item_type == "SPACER":
            # Draw a subtle divider line
            line_y = rect.center().y()
            line_color = QColor(c.get('border', '#E0DDD9'))
            line_color.setAlpha(40 if is_dark else 60)
            painter.setPen(QPen(line_color, 1))
            painter.drawLine(int(rect.left() + 18), int(line_y), int(rect.right() - 18), int(line_y))
            painter.restore()
            return

        # ── FOLDER ITEM ──
        item_rect = rect.adjusted(6, 2, -6, -2)
        
        if is_selected:
            # Subtle accent background with rounded rect
            sel_bg = QColor(c.get('active_item_bg', c.get('accent', 'rgba(0,0,0,0.05)')))
            painter.setBrush(QBrush(sel_bg))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(QRectF(item_rect), 8, 8)
            
            # Left accent bar (teal/primary gradient)
            bar_h = 18
            bar_y = item_rect.center().y() - bar_h / 2
            bar_rect = QRectF(item_rect.left(), bar_y, 3, bar_h)
            accent_color = primary_color
            painter.setBrush(QBrush(accent_color))
            painter.setPen(Qt.PenStyle.NoPen)
            bar_path = QPainterPath()
            bar_path.addRoundedRect(bar_rect, 1.5, 1.5)
            painter.drawPath(bar_path)
            
        elif is_hover:
            hover_bg = QColor(c.get('secondary', "#F5F5F4"))
            hover_bg.setAlpha(80 if is_dark else 100)
            painter.setBrush(QBrush(hover_bg))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(QRectF(item_rect), 8, 8)

        # ── Layout: [num] [icon] [text] ──
        content_x = item_rect.left() + 10
        
        # Number label (index prefix like "1.", "2.")
        display_text = index.data(Qt.ItemDataRole.DisplayRole) or ""
        num_text = ""
        folder_name = display_text
        
        # Extract number prefix if present (e.g. "1. ddsdfd" -> num="1", folder_name="ddsdfd")
        if display_text and len(display_text) > 2 and display_text[0].isdigit():
            parts = display_text.split('. ', 1)
            if len(parts) == 2 and parts[0].strip().isdigit():
                num_text = parts[0].strip()
                folder_name = parts[1]
        
        # Draw number
        if num_text:
            # JetBrains Mono, 10px, weight 500, opacity 0.4
            num_font = QFont("JetBrains Mono", 8)
            num_font.setWeight(QFont.Weight.Medium)
            painter.setFont(num_font)
            num_color = QColor(c.get('muted_foreground', '#4d5370'))
            if is_selected:
                num_color = QColor(primary_color)
                num_color.setAlpha(200)
            else:
                num_color.setAlpha(100)  # opacity ~0.4
            painter.setPen(num_color)
            num_rect = QRectF(content_x, rect.top(), 16, rect.height())
            painter.drawText(num_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, num_text)
            content_x += 22
        
        # Icon
        icon = index.data(Qt.ItemDataRole.DecorationRole)
        icon_size = 17
        if icon:
            icon_rect = QRectF(content_x, rect.center().y() - icon_size / 2, icon_size, icon_size)
            icon.paint(painter, icon_rect.toRect(), Qt.AlignmentFlag.AlignCenter, QIcon.Mode.Normal, QIcon.State.On)
        content_x += icon_size + 10
        
        # Text — DM Sans 13.5px, weight 400 (500 when active)
        text_w = item_rect.right() - content_x - 8
        if folder_name:
            # Text — DM Sans 10px, weight 500 (600 when active) for "thick" look
            # Color: Use foreground (bright) instead of muted to make it "glow" against dark
            txt_color = QColor(c.get('foreground', '#E8EAF2')) 
            if is_selected:
                txt_color = QColor(c.get('primary_foreground', '#FFFFFF'))
            
            painter.setPen(txt_color)
            # Use Inter SemiBold 11pt for "smooth bold" look (less thick than Bold)
            font = QFont("Inter", 11)
            font.setWeight(QFont.Weight.DemiBold) # Weight 600
            if is_selected:
                font.setPointSize(11) 
                
            painter.setFont(font)
            
            text_rect_f = QRectF(content_x, rect.top(), text_w, rect.height())
            elided = painter.fontMetrics().elidedText(folder_name, Qt.TextElideMode.ElideRight, int(text_rect_f.width()))
            painter.drawText(text_rect_f, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, elided)
            
        painter.restore()

class Sidebar(QWidget):
    folderSelected = pyqtSignal(str) # Emits folder ID
    noteSelected = pyqtSignal(str)   # NEW: Emits note ID
    createFolder = pyqtSignal(str, str) # folder_name, notebook_id
    deleteFolder = pyqtSignal(str)   # Emits folder ID
    renameFolder = pyqtSignal(str, str)  # Emits folder ID, new name
    exportFolder = pyqtSignal(str)   # Emits folder ID for export
    exportFolderWord = pyqtSignal(str) # NEW
    exportWhiteboard = pyqtSignal(str) # Emits folder ID for whiteboard export
    updateFolder = pyqtSignal(str, dict) # Emits folder ID, updates dict
    reorderFolder = pyqtSignal(str, int) # Emits folder ID, new position (index)
    restoreFolder = pyqtSignal(str, str) # Emits folder ID, trash_path
    restoreNote = pyqtSignal(str, str)   # NEW: note_id, trash_path
    permanentDeleteFolder = pyqtSignal(str) # Emits trash_path
    permanentDeleteNote = pyqtSignal(str)   # NEW: trash_path
    requestHighlightPreview = pyqtSignal(str) # folder_id
    requestPdfPreview = pyqtSignal(str) # folder_id
    toggleTheme = pyqtSignal(str)  # Emits chosen theme key
    wrapToggled = pyqtSignal(bool)
    createNotebook = pyqtSignal(str)
    deleteNotebook = pyqtSignal(str)
    lockToggled = pyqtSignal(bool)
    panelToggleRequest = pyqtSignal() # Phase 46
    sectionChanged = pyqtSignal(str) # Emits active section key (FOLDERS, RECENT, etc)
    removeFromRecentRequested = pyqtSignal(str)
    deleteNoteRequested = pyqtSignal(str)
    clearRecentRequested = pyqtSignal()
    emptyTrashRequest = pyqtSignal() # NEW: Phase 46.2

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        self.all_folders = []
        self.all_notebooks = []
        self.trashed_folders = []
        self.independent_trash_notes = [] # NEW: Notes directly in .trash
        self.sort_descending = True
        self.showing_archived = False
        self.theme_mode = "light" # Track current theme
        self.view_mode = VIEW_MODE_LIST
        self.current_icon_color = "#3D3A38" # Default for light
        
        # Collapsible Section State
        self.section_expanded = {
            "FAVORITES": True,
            "RECENT": True,
            "FOLDERS": True,
            "SYSTEM": False
        }
        
        self.active_section = "FOLDERS" # Current horizontal toggle section

        self._setup_header()
        self._setup_search()
        self._setup_view_toggles() # Horizontal Segmented Control
        self._setup_list()
        self._setup_internal_note_list() # NEW: For Recent/Trash direct views
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

        # Update Toggle Buttons (Text vs Icon)
        if hasattr(self, 'toggle_buttons'):
            # Switch to icons when narrow (< 260px)
            is_mini = width < 260
            
            c = styles.ZEN_THEME.get(self.theme_mode, styles.ZEN_THEME["light"])
            icon_color = c.get('sidebar_fg', c.get('foreground', '#3D3A38'))
            
            for key, btn in self.toggle_buttons.items():
                if is_mini:
                    if btn.text(): btn.setText("")
                    icon_name = "folder"
                    if key == "FAVORITES": icon_name = "heart"
                    elif key == "RECENT": icon_name = "clock"
                    elif key == "TRASH": icon_name = "trash_2"
                    
                    btn.setIcon(get_premium_icon(icon_name, color=icon_color))
                    btn.setIconSize(QSize(20, 20))
                    btn.setToolTip(key.title())
                    # Minimal padding for mini mode
                    btn.setStyleSheet(btn.styleSheet() + " QPushButton { padding: 6px 2px; }")
                else:
                    if not btn.text(): btn.setText(key.title())
                    btn.setIcon(QIcon())
                    btn.setToolTip("")
                    btn.setStyleSheet(btn.styleSheet().replace(" QPushButton { padding: 6px 2px; }", ""))

        # Hide search bar and controls if very narrow
        if hasattr(self, 'search_bar'):
            self.search_bar.setVisible(width > 140)
        if hasattr(self, 'nb_row'): # Container for selector
            self.nb_row.setVisible(width > 170)
        if hasattr(self, 'add_btn'):
            # Maybe show only icon for add button if narrowed?
            if width < 160:
                if self.add_btn.text(): self.add_btn.setText("")
                self.add_btn.setFixedWidth(36)
            else:
                if not self.add_btn.text(): self.add_btn.setText(" New Folder")
                self.add_btn.setMinimumWidth(100)
                self.add_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def _setup_header(self):
        header_container = QWidget()
        header_container.setObjectName("SidebarHeader") # For Global Styling
        self.header_layout = QVBoxLayout(header_container)
        self.header_layout.setContentsMargins(20, 20, 20, 16) # Exact zen-notes.html: 20px 20px 16px
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
        self.title_label = QLabel("ZEN NOTES")
        self.title_label.setObjectName("SidebarTitle")
        self.title_label.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        self.title_label.setStyleSheet("font-family: 'Playfair Display', serif; font-size: 18px; font-weight: 700; color: #3D3A38;")
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
        self.nb_row = QWidget()
        nb_layout = QHBoxLayout(self.nb_row)
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

        # Horizontal Controls (Small & Clean)
        self.nb_controls = QWidget()
        controls_layout = QHBoxLayout(self.nb_controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(4)
        
        # 1. Add Notebook
        self.add_folder_btn = QPushButton()
        self.add_folder_btn.setFixedSize(28, 28)
        self.add_folder_btn.setIconSize(QSize(14, 14))
        self.add_folder_btn.setToolTip("New Notebook")
        self.add_folder_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_folder_btn.clicked.connect(lambda: (pulse_button(self.add_folder_btn), self.prompt_new_notebook()))
        
        # 2. Delete Notebook
        self.delete_nb_btn = QPushButton()
        self.delete_nb_btn.setFixedSize(28, 28)
        self.delete_nb_btn.setIconSize(QSize(14, 14))
        self.delete_nb_btn.setToolTip("Delete Notebook")
        self.delete_nb_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.delete_nb_btn.clicked.connect(self._on_delete_notebook_clicked)

        # 3. Lock
        self.lock_btn = QPushButton()
        self.lock_btn.setCheckable(True)
        self.lock_btn.setFixedSize(28, 28)
        self.lock_btn.setIconSize(QSize(14, 14))
        self.lock_btn.setToolTip("Lock Navigation")
        self.lock_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lock_btn.toggled.connect(self._on_lock_toggled)

        controls_layout.addWidget(self.add_folder_btn)
        controls_layout.addWidget(self.delete_nb_btn)
        controls_layout.addWidget(self.lock_btn)
        
        nb_layout.addWidget(self.nb_controls)
        
        # --- End of Header --
        self.header_layout.addWidget(self.nb_row)
        self.layout.addWidget(header_container)

    def _setup_search(self):
        # Horizontal Layout: [ Search Bar ] [Sort] [Wrap] [Eye] [Mark]
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(16, 14, 16, 10) # zen-notes.html: padding: 14px 16px 0
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
                border-radius: 10px;
                padding: 6px 10px;
                font-family: 'Inter', sans-serif;
                font-size: 13px;
                background: rgba(0,0,0,0.03);
                border: 1px solid rgba(0,0,0,0.04);
                color: #3D3A38;
            }
            QLineEdit:focus {
                background: #FFFFFF;
                border: 1px solid rgba(123, 158, 135, 0.4);
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
        self.wrap_btn.setObjectName("ViewToggleBtn") # Standardize styling
        layout.addWidget(self.wrap_btn)
        
        # 2. Preview
        self.preview_btn = QPushButton()
        self.preview_btn.setIcon(get_premium_icon("eye"))
        self.preview_btn.setToolTip("Preview PDF")
        self.preview_btn.setFixedSize(icon_size, icon_size)
        self.preview_btn.setIconSize(QSize(16, 16))
        self.preview_btn.clicked.connect(lambda: self.requestPdfPreview.emit(str(self._get_active_folder_id()))) 
        self.preview_btn.setObjectName("ViewToggleBtn") # Standardize styling
        layout.addWidget(self.preview_btn)

        # 3. Highlight
        self.highlight_preview_btn = QPushButton()
        self.highlight_preview_btn.setIcon(get_premium_icon("sparkle"))
        self.highlight_preview_btn.setToolTip("Highlights")
        self.highlight_preview_btn.setFixedSize(icon_size, icon_size)
        self.highlight_preview_btn.setIconSize(QSize(16, 16))
        self.highlight_preview_btn.clicked.connect(lambda: self.requestHighlightPreview.emit(str(self._get_active_folder_id())))
        self.highlight_preview_btn.setObjectName("ViewToggleBtn") # Standardize styling
        layout.addWidget(self.highlight_preview_btn)

        self.layout.addWidget(container)

    def _setup_view_toggles(self):
        """Create a horizontal segmented control for switching categories."""
        container = QWidget()
        container.setObjectName("SidebarToggleContainer")
        layout = QHBoxLayout(container)
        layout.setContentsMargins(16, 4, 16, 10)
        layout.setSpacing(4)
        
        self.toggle_buttons = {}
        sections = [
            ("Folders", "FOLDERS"),
            ("Favorites", "FAVORITES"),
            ("Recent", "RECENT"),
            ("Trash", "TRASH")
        ]
        
        # Style for the segmented buttons
        button_style = """
            QPushButton {
                border: none;
                border-radius: 8px;
                padding: 6px 12px;
                font-family: 'Inter', sans-serif;
                font-size: 12px;
                font-weight: 500;
                color: #64748B;
                background: transparent;
            }
            QPushButton:hover {
                background: rgba(0,0,0,0.03);
            }
            QPushButton[active="true"] {
                color: #3D3A38;
                background: rgba(0,0,0,0.06);
                font-weight: 600;
            }
        """
        
        for label, key in sections:
            btn = QPushButton(label)
            btn.setCheckable(False)
            btn.setProperty("section_key", key)
            btn.setProperty("active", "true" if key == self.active_section else "false")
            btn.setStyleSheet(button_style)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, k=key: self.set_active_section(k))
            
            layout.addWidget(btn)
            self.toggle_buttons[key] = btn
            
        self.layout.addWidget(container)
        
        # Trigger initial update
        self.resizeEvent(None)

    def _setup_internal_note_list(self):
        """Hidden note list for Recent/Trash 'Zen' views."""
        from ui.note_card_delegate import NoteCardDelegate
        
        # 1. Internal Stacked Widget to support List/Grid inside the Zen View
        self.internal_stack = QStackedWidget()
        
        # List Mode
        self.internal_notes_list = QListWidget()
        self.internal_notes_list.setObjectName("SidebarNoteItems")
        self.internal_notes_list.setSpacing(4)
        self.internal_notes_list.itemClicked.connect(self._on_internal_note_clicked)
        self.internal_notes_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.internal_notes_list.customContextMenuRequested.connect(self.show_internal_notes_context_menu)
        
        from ui.note_card_delegate import NoteCardDelegate
        self.note_delegate = NoteCardDelegate(self.internal_notes_list)
        self.internal_notes_list.setItemDelegate(self.note_delegate)
        
        # Grid Mode
        self.internal_notes_grid = QListWidget()
        self.internal_notes_grid.setObjectName("SidebarNoteGrid")
        self.internal_notes_grid.setViewMode(QListWidget.ViewMode.IconMode)
        self.internal_notes_grid.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.internal_notes_grid.setSpacing(8)
        self.internal_notes_grid.itemClicked.connect(self._on_internal_note_clicked)
        self.internal_notes_grid.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.internal_notes_grid.customContextMenuRequested.connect(self.show_internal_notes_context_menu)
        
        self.grid_delegate = NoteCardDelegate(self.internal_notes_grid, is_grid=True)
        self.internal_notes_grid.setItemDelegate(self.grid_delegate)
        
        self.internal_stack.addWidget(self.internal_notes_list)
        self.internal_stack.addWidget(self.internal_notes_grid)
        
        # Add to main stack as index 2
        self.stacked_list.addWidget(self.internal_stack)

    def show_internal_notes_context_menu(self, pos):
        """Context menu for Recent/Trash notes in sidebar."""
        widget = self.sender()
        item = widget.itemAt(pos)
        if not item: return
        
        note_id = item.data(Qt.ItemDataRole.UserRole)
        if not note_id: return
        
        from PyQt6.QtWidgets import QMenu
        from PyQt6.QtGui import QAction
        
        menu = QMenu(self)
        
        if self.active_section == "RECENT":
            remove_act = menu.addAction("Remove from Recent")
            remove_act.triggered.connect(lambda: self.removeFromRecentRequested.emit(note_id))
            
            menu.addSeparator()
            
            delete_act = menu.addAction("Move to Trash")
            delete_act.triggered.connect(lambda: self.deleteNoteRequested.emit(note_id))
            
            menu.addSeparator()
            
            clear_act = menu.addAction("Clear All Recent")
            clear_act.triggered.connect(lambda: self.clearRecentRequested.emit())
            
        elif self.active_section == "TRASH":
            restore_act = menu.addAction(get_premium_icon("rotate_ccw", color="#10B981"), "Restore Note")
            delete_perm_act = menu.addAction(get_premium_icon("delete", color="#EF4444"), "Delete Permanently")
            
            menu.addSeparator()
            empty_trash_act = menu.addAction(get_premium_icon("trash", color="#EF4444"), "Empty Trash")
            
            action = menu.exec(widget.mapToGlobal(pos))
            if action == restore_act:
                self.restoreNote.emit(note_id, "") # Trash path lookup happens in MainWindow
            elif action == delete_perm_act:
                # We need trash path for permanent delete
                # Simple notes in sidebar have it in UserRole+1 or we search
                note = item.data(Qt.ItemDataRole.UserRole + 1)
                t_path = getattr(note, '_trash_path', None)
                if t_path: self.permanentDeleteNote.emit(t_path)
            elif action == empty_trash_act:
                self.emptyTrashRequest.emit()

    def _on_internal_note_clicked(self, item):
        note_id = item.data(Qt.ItemDataRole.UserRole)
        if note_id:
            self.noteSelected.emit(note_id)

    def set_active_section(self, section_key):
        """Update active button state and refresh the list."""
        if self.active_section == section_key:
            return
            
        self.active_section = section_key
        
        # Update button properties for styling
        for key, btn in self.toggle_buttons.items():
            btn.setProperty("active", "true" if key == self.active_section else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
            btn.update()
            
        self.sectionChanged.emit(section_key)
        self.refresh_list()

    def populate_internal_notes(self, notes):
        """Update the sidebar's note list/grid (Index 2)."""
        self.internal_notes_list.clear()
        self.internal_notes_grid.clear()
        
        from PyQt6.QtWidgets import QListWidgetItem
        from ui.color_delegate import COLOR_ROLE
        
        for idx, note in enumerate(notes, 1):
            # 1. List Item
            item_list = QListWidgetItem(f"{idx}. {note.title}")
            item_list.setData(Qt.ItemDataRole.UserRole, note.id)
            item_list.setData(Qt.ItemDataRole.UserRole + 1, note) # For delegate
            if getattr(note, 'color', None):
                item_list.setData(COLOR_ROLE, note.color)
            self.internal_notes_list.addItem(item_list)
            
            # 2. Grid Item
            item_grid = QListWidgetItem(f"{idx}. {note.title}")
            item_grid.setData(Qt.ItemDataRole.UserRole, note.id)
            item_grid.setData(Qt.ItemDataRole.UserRole + 1, note)
            if getattr(note, 'color', None):
                item_grid.setData(COLOR_ROLE, note.color)
            self.internal_notes_grid.addItem(item_grid)

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
        self.list_tree.setIndentation(0) # Remove default branch area (fixes blue block artifact)
        self.list_tree.setAnimated(True)
        self.list_tree.setRootIsDecorated(False) # We draw our own chevrons in the delegate
        self.list_tree.setUniformRowHeights(False) # REQUIRED for variable height items (spacers/headers)
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
        is_dark = mode in ("dark", "dark_blue", "ocean_depth", "noir_ember")
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
        
        # Update Brand Typography
        self.title_label.setStyleSheet(f"font-family: 'Playfair Display', serif; font-size: 18px; font-weight: 700; color: {icon_color};")
        
        # Update Bottom Icons
        self.panel_toggle_btn.setIcon(get_premium_icon("panel_toggle", color=icon_color))
        
        # Update View Toggle Icon
        if getattr(self, 'view_mode', VIEW_MODE_LIST) == VIEW_MODE_GRID:
            self.view_toggle_btn.setIcon(get_premium_icon("layout_list", color=icon_color))
        else:
            self.view_toggle_btn.setIcon(get_premium_icon("layout_grid", color=icon_color))
            
        # Selectors & Input
        self.nb_selector.setStyleSheet(f"""
            QComboBox {{ 
                background: {c.get('card', '#FFFFFF')}; 
                color: {c['foreground']}; 
                border: 1px solid {c.get('border', '#E0DDD9')}; 
                border-radius: 12px; 
                padding: 6px 12px; 
                font-family: 'Inter', sans-serif;
                font-size: 12px;
                font-weight: 500;
                min-height: 34px;
                max-height: 34px;
            }}
            QComboBox:hover {{
                border-color: {c.get('primary', '#7B9E87')};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
        """)

        # Sidebar Header Separation
        self.sidebar_header_widget = self.header_layout.parentWidget()
        if self.sidebar_header_widget:
            self.sidebar_header_widget.setStyleSheet(f"#SidebarHeader {{ border-bottom: 1px solid {c.get('border', '#E0DDD9')}44; }}") # Subtle 44 alpha

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
        
        # POLISH: Ensure the header container itself has a subtle separation line if needed
        # but Zen mode usually prefers clean space. Let's add a very subtle border-bottom.
        # self.header_layout.parentWidget().setStyleSheet(f"border-bottom: 1px solid {c.get('border', '#EEE')};")
        
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
        
        # Add Button icon - dark on bright gradient for dark themes, white on solid primary for light
        add_icon_color = "#0d1219" if is_dark else "#FFFFFF"
        self.add_btn.setIcon(get_premium_icon("plus", color=add_icon_color))
        
        # New Folder Button - Premium Zen look (teal-to-blue gradient)
        primary = c.get('primary', '#7B9E87')
        primary_fg = c.get('primary_foreground', '#FFFFFF')
        
        # Use a gradient for dark themes, solid primary for light themes
        if is_dark:
            btn_bg = 'qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3dd6c4, stop:0.5 #4db8e8, stop:1 #5b9cf6)'
            btn_fg = '#0d1219'
            btn_hover_bg = 'qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #35c4b3, stop:0.5 #44a8d8, stop:1 #518ce6)'
        else:
            btn_bg = primary
            btn_fg = primary_fg
            btn_hover_bg = f'{primary}DD'
        
        self.add_btn.setStyleSheet(f"""
            QPushButton#NewFolderBtn {{
                background: {btn_bg};
                color: {btn_fg};
                border: none;
                border-radius: 12px;
                padding: 8px 16px;
                font-family: 'Inter', sans-serif;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton#NewFolderBtn:hover {{
                background: {btn_hover_bg};
            }}
            QPushButton#NewFolderBtn:pressed {{
                background: {btn_bg};
                margin-top: 0px;
                margin-left: 0px;
            }}
        """)
        
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
        bottom_main_layout.setContentsMargins(16, 14, 16, 18) # zen-notes.html: padding: 14px 16px 18px
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
        
        # Capture current selection for sync
        current_id = None
        if self.list_widget == self.list_tree:
            item = self.list_tree.currentItem()
            if item: current_id = item.data(0, Qt.ItemDataRole.UserRole)
        elif self.list_widget == self.list_grid:
            item = self.list_grid.currentItem()
            if item: current_id = item.data(Qt.ItemDataRole.UserRole)

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
        
        # Restore selection
        if current_id:
            self.select_folder_by_id(current_id)

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
        
    def load_trash(self, folders, independent_notes):
        """Update the list of trashed folders and independent notes, then refresh UI."""
        self.trashed_folders = folders
        self.independent_trash_notes = independent_notes
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
            # Note: load_data already filters out folders starting with '.' (like .trash)
            # We don't need to manually exclude "trash" here anymore as it prevents users
            # from managing folders they named "Trash".

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
        
        # Define favorites for use in both Grid and Tree views
        fav_folders = [f for f in active_folders if f.is_pinned]

        # Build Lists for the Grid View too (Flat representation for Grid)
        all_display_folders = []
        if ideas_folder: all_display_folders.append(ideas_folder)
        all_display_folders.extend(active_folders)
        # Not showing Archived in Grid for now to keep it clean, or we can add them at bottom.

        # --- UI BUILDING ---
        
        # 0. Header/Footer Visibility Controls (Hide for TRASH)
        is_trash_section = self.active_section == "TRASH"
        if hasattr(self, 'nb_controls'):
            self.nb_controls.setVisible(not is_trash_section)
        if hasattr(self, 'add_btn'):
            self.add_btn.setVisible(not is_trash_section)

        # Recent is handled via internal note stack
        if self.active_section == "RECENT":
            self.stacked_list.setCurrentIndex(2) 
            internal_idx = 1 if self.view_mode == VIEW_MODE_GRID else 0
            self.internal_stack.setCurrentIndex(internal_idx)
            self.list_tree.clear()
            self.list_grid.clear()
            return

        if self.view_mode == VIEW_MODE_GRID:
            self.stacked_list.setCurrentIndex(1)
            self.list_widget = self.list_grid
            
            # Population logic for Grid
            display_folders = []
            if self.active_section == "FAVORITES": display_folders = fav_folders
            elif self.active_section == "FOLDERS": display_folders = active_folders
            elif self.active_section == "TRASH": display_folders = self.trashed_folders
            else: display_folders = active_folders

            for f in display_folders:
                item = QListWidgetItem(f.name)
                item.setData(Qt.ItemDataRole.UserRole, f.id)
                item.setData(Qt.ItemDataRole.UserRole + 1, f)
                
                is_trashed = getattr(f, '_trash_path', None) is not None
                icon_color = getattr(f, 'color', self.current_icon_color)
                if is_trashed: icon_color = "#94A3B8"
                
                item.setIcon(get_premium_icon("trash_2" if is_trashed else "folder", color=icon_color))
                self.list_grid.addItem(item)
        else:
            # Tree View (List Mode)
            self.stacked_list.setCurrentIndex(0)
            self.list_widget = self.list_tree
            
            if self.active_section == "TRASH":
                # Hierarchical Trash View
                folder_items = {} # Map folder_id -> QTreeWidgetItem
                folder_name_map = {} # Fallback: Map folder_name.lower() -> QTreeWidgetItem
                
                for folder in self.trashed_folders:
                    folder_item = QTreeWidgetItem(self.list_tree)
                    folder_item.setText(0, folder.name)
                    folder_item.setData(0, Qt.ItemDataRole.UserRole, folder.id)
                    folder_item.setData(0, Qt.ItemDataRole.UserRole + 1, folder)
                    folder_item.setIcon(0, get_premium_icon("trash_2", color="#94A3B8"))
                    folder_item.setExpanded(True) # NEW: Auto-expand trashed folders
                    folder_items[folder.id] = folder_item
                    folder_name_map[folder.name.lower().strip()] = folder_item
                    
                    for note in getattr(folder, 'notes', []):
                        note_item = QTreeWidgetItem(folder_item)
                        note_item.setText(0, note.title)
                        note_item.setData(0, Qt.ItemDataRole.UserRole, note.id)
                        note_item.setData(0, Qt.ItemDataRole.UserRole + 1, note)
                        note_item.setIcon(0, get_premium_icon("note", color="#94A3B8"))
                
                # Independent Trashed Notes (Check for trashed parent folders)
                for note in self.independent_trash_notes:
                    parent_id = getattr(note, 'trash_original_folder_id', None)
                    parent_name = getattr(note, 'trash_original_folder_name', '').lower().strip()
                    
                    parent_item = folder_items.get(parent_id)
                    if not parent_item and parent_name:
                        parent_item = folder_name_map.get(parent_name) # Fallback to name match
                    
                    if parent_item:
                        # Nest under trashed folder
                        note_item = QTreeWidgetItem(parent_item)
                        note_item.setText(0, note.title)
                    else:
                        # Keep at top level (Independent/Orphan)
                        note_item = QTreeWidgetItem(self.list_tree)
                        orig_nb = getattr(note, 'trash_original_folder_name', 'Personal')
                        note_item.setText(0, f"{note.title} (from {orig_nb})")
                        
                    note_item.setData(0, Qt.ItemDataRole.UserRole, note.id)
                    note_item.setData(0, Qt.ItemDataRole.UserRole + 1, note)
                    note_item.setIcon(0, get_premium_icon("note", color="#94A3B8"))
                    
                if archived_folders:
                    arch_head = QTreeWidgetItem(self.list_tree)
                    arch_head.setText(0, f"Archived ({len(archived_folders)})")
                    arch_head.setIcon(0, get_premium_icon("archive", color="#F59E0B"))
                    for af in archived_folders:
                        item = QTreeWidgetItem(arch_head)
                        item.setText(0, af.name)
                        item.setData(0, Qt.ItemDataRole.UserRole, af.id)
                        item.setData(0, Qt.ItemDataRole.UserRole + 1, af)
                        item.setIcon(0, get_premium_icon("folder", color="#94A3B8"))
            else:
                # Standard Sidebar Population Logic
                if self.active_section == "FAVORITES":
                    if ideas_folder:
                        self._add_list_node("Ideas & Sparks", ideas_folder, icon="heart", icon_color="#f472b6", count=getattr(ideas_folder, 'note_count', None))
                    for f in fav_folders:
                        self._add_list_node(f.name, f, count=getattr(f, 'note_count', None))
                elif self.active_section == "FOLDERS":
                    for i, f in enumerate(active_folders, 1):
                        self._add_list_node(f.name, f, index_prefix=f"{i}. ", count=getattr(f, 'note_count', None))


    def _add_list_node(self, text, data=None, is_header=False, is_spacer=False, icon="folder", icon_color=None, count=None, index_prefix="", section_key=None, is_expanded=True):
        item = QTreeWidgetItem([text])
        
        if is_spacer:
            item.setData(0, Qt.ItemDataRole.UserRole + 2, "SPACER")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.list_tree.addTopLevelItem(item)
            return

        if is_header:
            item.setData(0, Qt.ItemDataRole.UserRole + 2, "SECTION_HEADER")
            # Enable item so it can be clicked, but maybe not selectable? 
            # We handle selection manually.
            item.setFlags(Qt.ItemFlag.ItemIsEnabled) 
            
            if section_key:
                item.setData(0, Qt.ItemDataRole.UserRole + 3, section_key)
                item.setData(0, Qt.ItemDataRole.UserRole + 4, is_expanded)
            
            item.setText(0, text.upper())
            # Premium Header Styling — JetBrains Mono matching delegate
            font = item.font(0)
            font.setFamily("JetBrains Mono")
            font.setPointSize(7)
            font.setWeight(500)
            font.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 116)
            item.setFont(0, font)
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
            # CRITICAL FALLBACK: Use current_icon_color if folder has no color
            folder_color = getattr(data, 'color', None)
            final_color = icon_color if icon_color else (folder_color if folder_color else self.current_icon_color)
        
        item.setIcon(0, get_premium_icon(final_icon, color=final_color, size=QSize(36, 36), thick=True))
        
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
            # Check for Section Header Toggle
            item_type = item.data(0, Qt.ItemDataRole.UserRole + 2)
            if item_type == "SECTION_HEADER":
                section_key = item.data(0, Qt.ItemDataRole.UserRole + 3)
                if section_key:
                    self.section_expanded[section_key] = not self.section_expanded.get(section_key, True)
                    self.refresh_list()
                    return

            data = item.data(0, Qt.ItemDataRole.UserRole)
            note_obj = item.data(0, Qt.ItemDataRole.UserRole + 1) # NEW
        else:
            data = item.data(Qt.ItemDataRole.UserRole)
            note_obj = item.data(Qt.ItemDataRole.UserRole + 1) # NEW
            
        if not data: return
        
        if isinstance(data, str) and data.startswith("NOTEBOOK:"):
            # ... (nb logic) ...
            nb_id = data.split(":")[1]
            idx = self.nb_selector.findData(nb_id)
            if idx >= 0:
                self.nb_selector.setCurrentIndex(idx)
            return
            
        if data == "ARCHIVED_ROOT":
            if isinstance(item, QTreeWidgetItem):
                item.setExpanded(not item.isExpanded())
            return
            
        # Emit folder or note selection
        from models.note import Note
        if isinstance(note_obj, Note):
            self.noteSelected.emit(note_obj.id)
        else:
            # If in Trash, clicking a folder should just toggle expansion and NOT emit folderSelected
            # because we want the middle panel to remain empty for trashed items.
            if self.active_section == "TRASH":
                if isinstance(item, QTreeWidgetItem):
                    item.setExpanded(not item.isExpanded())
                # Still emit a fake select_folder event to clear MainWindow middle panel
                self.folderSelected.emit("TRASH_ROOT") 
            else:
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
        # Check if it's a trashed folder
        folder = next((f for f in self.trashed_folders if f.id == folder_id), None)
        if folder:
            trash_path = getattr(folder, '_trash_path', None)
            if trash_path:
                if QMessageBox.question(self, "Delete Permanently", f"Are you sure you want to permanently delete folder '{folder.name}'?\nAll its notes will be gone forever.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
                    self.permanentDeleteFolder.emit(trash_path)
            return

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

    def prompt_change_folder_page_size(self, folder_id):
        folder = next((f for f in self.all_folders if f.id == folder_id), None)
        if not folder: return
        
        from ui.zen_dialog import PageSizeDialog
        current_size = getattr(folder, 'page_size', 'free')
        new_size, ok = PageSizeDialog.getPageSize(self, current_size, self.theme_mode)
        if ok:
            self.updateFolder.emit(folder_id, {"page_size": new_size})

    def prompt_change_folder_bg_color(self, folder_id):
        """Open color picker for folder editor background."""
        from PyQt6.QtWidgets import QColorDialog
        from PyQt6.QtGui import QColor
        
        folder = next((f for f in self.all_folders if f.id == folder_id), None)
        # Check trashed too just in case
        if not folder:
             folder = next((f for f in self.trashed_folders if f.id == folder_id), None)
             
        if not folder: return
        
        initial_color = getattr(folder, 'editor_background_color', '#FFFFFF') or '#FFFFFF'
        initial = QColor(initial_color)
        
        col = QColorDialog.getColor(initial, self, "Select Folder Editor Background")
        if col.isValid():
            # Emit signal to update folder metadata
            self.updateFolder.emit(folder_id, {"editor_background_color": col.name()})

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

        from models.note import Note
        if isinstance(data, Note):
            # Special Context Menu for Trashed Notes in Sidebar
            m_color = self.current_icon_color
            restore_act = menu.addAction(get_premium_icon("rotate_ccw", color="#10B981"), "Restore Item")
            delete_act = menu.addAction(get_premium_icon("delete", color="#EF4444"), "Permanently Delete Item")
            
            action = menu.exec(active_widget.mapToGlobal(pos))
            if action == restore_act:
                # We need a special signal for note restoration or reuse existing ones
                # For now, let's assume we might need self.restoreNote.emit(data.id, data._trash_path)
                # But let's check if Sidebar has restoreNote. If not, add it.
                if hasattr(self, 'restoreNote'):
                    self.restoreNote.emit(data.id, getattr(data, '_trash_path', ""))
            elif action == delete_act:
                if hasattr(self, 'permanentDeleteNote'):
                    self.permanentDeleteNote.emit(getattr(data, '_trash_path', ""))
            return

        # Folder Context Menu (Standard)
        if data in ["ALL_NOTEBOOKS_ROOT", "ARCHIVED_ROOT", "RECENT_ROOT"]: 
            return
            
        if data == "TRASH_ROOT":
            empty_trash_act = menu.addAction(get_premium_icon("trash", color="#EF4444"), "Empty Trash")
            action = menu.exec(active_widget.mapToGlobal(pos))
            if action == empty_trash_act:
                self.emptyTrashRequest.emit()
            return

        folder_id = data
        folder = next((f for f in self.all_folders if f.id == folder_id), None)
        # Check trashed folders too
        if not folder:
            folder = next((f for f in self.trashed_folders if f.id == folder_id), None)
            
        if not folder: return

        # Use current themed icon color for context menu icons
        m_color = self.current_icon_color

        # Reproduce existing folder options
        rename_act = menu.addAction(get_premium_icon("edit", color=m_color), "Rename Folder")
        
        set_cover_act = menu.addAction(get_premium_icon("image", color=m_color), "Set Cover Image...")
        edit_desc_act = menu.addAction(get_premium_icon("align_left", color=m_color), "Edit Description...")

        color_act = menu.addAction(get_premium_icon("palette", color=m_color), "Change Color")
        
        # NEW: Folder Background Color
        bg_color_act = menu.addAction(get_premium_icon("layout", color=m_color), "Set Editor Background")
        bg_color_act.triggered.connect(lambda: self.prompt_change_folder_bg_color(folder_id))
        
        # NEW: Folder Page Size
        page_size_act = menu.addAction(get_premium_icon("file_text", color=m_color), "Set Folder Page Size")
        page_size_act.triggered.connect(lambda: self.prompt_change_folder_page_size(folder_id))
        
        # Priority Submenu
        prio_menu = menu.addMenu(get_premium_icon("flag", color=m_color), "Set Priority")
        p0 = prio_menu.addAction("None")
        p1 = prio_menu.addAction("❶ High")
        p2 = prio_menu.addAction("❷ Medium")
        p3 = prio_menu.addAction("❸ Low")

        pin_text = "Remove from Favorites" if folder.is_pinned else "Add to Favorites"
        # Fallback if heart_off not exists, use heart
        pin_act = menu.addAction(get_premium_icon("heart", color=m_color), pin_text)
        
        arch_text = "Unarchive Folder" if folder.is_archived else "Archive Folder"
        arch_act = menu.addAction(get_premium_icon("folder_archived", color=m_color), arch_text)
        
        menu.addSeparator()
        export_act = menu.addAction(get_premium_icon("export", color=m_color), "Export Folder to PDF")
        export_word_act = menu.addAction(get_premium_icon("doc", color=m_color), "Export Folder to Word") # NEW
        
        menu.addSeparator()
        
        is_trashed = getattr(folder, '_trash_path', None) is not None
        if is_trashed:
            restore_act = menu.addAction(get_premium_icon("rotate_ccw", color=m_color), "Restore Folder")
            delete_act = menu.addAction(get_premium_icon("delete", color="#EF4444"), "Permanently Delete Folder")
            menu.addSeparator()
            empty_trash_act = menu.addAction(get_premium_icon("trash", color="#EF4444"), "Empty Trash")
        else:
            restore_act = None
            empty_trash_act = None
            delete_act = menu.addAction(get_premium_icon("delete", color=m_color), "Move to Trash")

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
        elif empty_trash_act and action == empty_trash_act:
            self.emptyTrashRequest.emit()
        elif restore_act and action == restore_act:
            trash_path = getattr(folder, '_trash_path', None)
            if trash_path:
                self.restoreFolder.emit(folder_id, trash_path)
        elif action in [p0, p1, p2, p3]:
            p_val = [p0, p1, p2, p3].index(action)
            self.updateFolder.emit(folder_id, {"priority": p_val})

    def select_folder_by_id(self, folder_id):
        self.list_widget.clearSelection()
        
        if self.list_widget == self.list_tree:
            from PyQt6.QtWidgets import QTreeWidgetItemIterator
            iterator = QTreeWidgetItemIterator(self.list_tree)
            while iterator.value():
                item = iterator.value()
                if item.data(0, Qt.ItemDataRole.UserRole) == folder_id:
                    self.list_tree.setCurrentItem(item)
                    if item.parent():
                        item.parent().setExpanded(True)
                    break
                iterator += 1
        elif self.list_widget == self.list_grid:
            for i in range(self.list_grid.count()):
                item = self.list_grid.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == folder_id:
                    self.list_grid.setCurrentItem(item)
                    break

    def toggle_archived_view(self):
        self.showing_archived = not self.showing_archived
        # Update UI if needed, refresh list
        self.refresh_list()
