from PyQt6.QtWidgets import QStyledItemDelegate, QStyle
from PyQt6.QtCore import Qt, QRect, QSize, QPoint, QRectF, QPointF
from PyQt6.QtGui import QPainter, QColor, QFont, QPixmap, QBrush, QPen, QPainterPath, QIcon
from models.note import Note
from util.icon_factory import get_premium_icon
import ui.styles as styles
import os

class NoteCardDelegate(QStyledItemDelegate):
    def __init__(self, parent=None, theme_mode="light", is_grid=False):
        super().__init__(parent)
        self.theme_mode = theme_mode
        self.is_grid = is_grid
        self.cover_cache = {} # path -> QPixmap

    def set_theme_mode(self, mode):
        self.theme_mode = mode

    def sizeHint(self, option, index):
        if option.widget:
            viewport = option.widget.viewport()
            total_width = viewport.width()
            
            # Margins
            margin = 16 
            available_width = total_width - margin
            
            # Clamp width but keep it responsive
            card_width = min(420, max(200, available_width))
            
            # 110px height is consistent for horizontal layout
            return QSize(int(card_width), 110)
        return QSize(250, 110)

    def paint(self, painter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 1. Setup Colors based on Theme
        c = styles.ZEN_THEME.get(self.theme_mode, styles.ZEN_THEME["light"])
        is_dark = self.theme_mode == "dark"
        
        # Default Card Colors
        bg_color = QColor(c.get('card', "#FFFFFF"))
        text_color = QColor(c.get('foreground', "#3D3A38"))
        sub_text_color = QColor(c.get('muted_foreground', "#8D8682"))
        border_color = QColor(c.get('border', "#E0DDD9"))
        
        if option.state & QStyle.StateFlag.State_Selected:
            # Dynamic Theme Colors (Fixes "Orange" request for Dark Mode and supports all others)
            bg_color = QColor(c.get('selection_bg', c['secondary']))
            border_color = QColor(c.get('ring', c['primary']))
        
        if option.state & QStyle.StateFlag.State_MouseOver:
             border_color = QColor(c.get('ring', c['primary']))

        # 2. Draw Card Background (Balanced stretching)
        rect = option.rect
        # Centering internal margin logic:
        # If the rect is wider than our intended max (from sizeHint), 
        # let's center the card inside it.
        # But sizeHint already does the heavy lifting, so we just use the rect with standard padding.
        card_rect = rect.adjusted(6, 4, -6, -4) 
        
        path = QPainterPath()
        path.addRoundedRect(QRectF(card_rect), 10, 10) # Slightly tighter radius
        
        painter.setPen(QPen(border_color, 1))
        painter.setBrush(QBrush(bg_color))
        painter.drawPath(path)
        
        # 3. Data Extraction
        note = index.data(Qt.ItemDataRole.UserRole + 1)
        if not note: 
            painter.restore()
            return

        content_rect = card_rect.adjusted(10, 10, -10, -10)
        
        # Consistent Horizontal Layout for all modes
        img_width = 70 if self.is_grid else 80
        image_rect = QRectF(content_rect.x(), content_rect.y(), img_width, content_rect.height())
        text_x = content_rect.x() + img_width + 12
        text_width = content_rect.width() - img_width - 12
        text_rect = QRectF(text_x, content_rect.y(), text_width, content_rect.height())

        # Checkbox Rect (Top Right) - Phase 44
        cb_size = 18
        cb_padding = 10
        # Position relative to card_rect
        self.cb_rect = QRectF(card_rect.right() - cb_size - cb_padding, card_rect.top() + cb_padding, cb_size, cb_size)
        
        # Draw Checkbox
        painter.save()
        cb_border = QColor(c.get('border', "#E0DDD9"))
        cb_bg = QColor(c.get('input', "#FFFFFF"))
        
        is_closed = bool(getattr(note, 'closed_at', None))
        
        painter.setPen(QPen(cb_border, 1.5))
        if is_closed:
            # Filled if closed
            painter.setBrush(QBrush(QColor(c.get('primary', "#7B9E87")))) # Use Primary for check
            painter.drawRoundedRect(self.cb_rect, 4, 4)
            # Draw Checkmark
            painter.setPen(QPen(Qt.GlobalColor.white, 2))
            # simple checkmark
            p1 = QPointF(self.cb_rect.left() + 4, self.cb_rect.center().y())
            p2 = QPointF(self.cb_rect.center().x() - 1, self.cb_rect.bottom() - 5)
            p3 = QPointF(self.cb_rect.right() - 4, self.cb_rect.top() + 5)
            painter.drawPolyline([p1, p2, p3])
        else:
            painter.setBrush(QBrush(cb_bg))
            painter.drawRoundedRect(self.cb_rect, 4, 4)
        painter.restore()

        # 5. Draw Image or Placeholder
        has_image = False
        if getattr(note, 'cover_image', None) and os.path.exists(note.cover_image):
            pixmap = self.cover_cache.get(note.cover_image)
            if not pixmap:
                pixmap = QPixmap(note.cover_image)
                if not pixmap.isNull():
                    # Cache slightly larger to avoid artifacts
                    pixmap = pixmap.scaled(QSize(int(img_width * 2), int(img_width * 2)), 
                                         Qt.AspectRatioMode.KeepAspectRatioByExpanding, 
                                         Qt.TransformationMode.SmoothTransformation)
                    self.cover_cache[note.cover_image] = pixmap
            
            if pixmap and not pixmap.isNull():
                has_image = True
                painter.save()
                
                # Aspect Fill logic
                target_rect = image_rect
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
                img_path.addRoundedRect(target_rect, 6, 6) # Inner radius
                painter.setClipPath(img_path)
                painter.drawPixmap(target_rect, pixmap, source_rect)
                painter.restore()

        if not has_image:
            # Draw Placeholder
            painter.save()
            placeholder_color = QColor(c.get('muted', "#F2F0ED"))
            icon_color = QColor(c.get('muted_foreground', "#8D8682"))
            
            p_path = QPainterPath()
            p_path.addRoundedRect(image_rect, 6, 6)
            p_path.setFillRule(Qt.FillRule.WindingFill)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(placeholder_color)
            painter.drawPath(p_path)
            
            # Draw Icon using get_premium_icon
            # We want a pixmap of the icon
            icon_size = 24
            icon_pixmap = get_premium_icon("note", color=icon_color).pixmap(icon_size, icon_size)
            
            # Center the icon
            icon_x = image_rect.center().x() - icon_size / 2
            icon_y = image_rect.center().y() - icon_size / 2
            painter.drawPixmap(QPointF(icon_x, icon_y), icon_pixmap)

            painter.restore()

        # 6. Draw Text
        # Title (Reduced Size Phase 42)
        title_font = QFont("Inter", 9, QFont.Weight.Bold)
        painter.setFont(title_font)
        
        # If closed, dim the text or add strike-through? 
        # User said "lock and show closed data". Let's dim it.
        if is_closed:
            painter.setPen(sub_text_color)
        else:
            painter.setPen(text_color)
        
        # Numbering
        number = index.row() + 1
        raw_title = note.title if note.title else "Untitled"
        title_text = f"{number}. {raw_title}"
        
        # Calculate bounding rect but limit height
        title_bound = painter.boundingRect(QRectF(text_rect), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap, title_text)
        
        # Clamp title height to max 2 lines (approx 28px) for more compact look
        max_title_height = 28 
        actual_title_height = min(title_bound.height(), max_title_height)
        
        title_rect_draw = QRectF(text_rect.x(), text_rect.y(), text_rect.width() - 25, actual_title_height)
        
        # Use ElideRight if it exceeds max height?
        # DrawText doesn't support vertical elision easily with TextWordWrap. 
        # But we can just clip it or let it be. 
        # Better: if height > max, we might want to elide the text itself.
        # For now, let's just let drawText handle it within the rect, it might clip bottom lines.
        # Actually QPainter.drawText with a rect will clip if text doesn't fit? No, it usually spills unless clipped.
        # We can set a clip rect.
        
        painter.save()
        painter.setClipRect(title_rect_draw)
        painter.drawText(title_rect_draw, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap, title_text)
        painter.restore()
        
        # Date Footer Prep (Phase 44: Support 3 lines if closed)
        meta_lines = 3 if is_closed else 2
        footer_height = (meta_lines * 12) + 2
        date_y = content_rect.bottom() - footer_height + 2
        
        # Adjust description height (Force Redefine)
        desc_top = text_rect.y() + actual_title_height + 4
        # Calculate footer space dynamically
        desc_h = text_rect.height() - actual_title_height - footer_height - 8
        desc_rect = QRectF(text_rect.x(), desc_top, text_rect.width(), max(0, desc_h))

        
        # Redraw description with new rect
        desc_text = getattr(note, 'description', "")
        
        if desc_text:
            desc_font = QFont("Inter", 8)
            painter.setFont(desc_font)
            painter.setPen(sub_text_color)
            elided_desc = painter.fontMetrics().elidedText(desc_text, Qt.TextElideMode.ElideRight, int(desc_rect.width() * 2.5)) 
            painter.drawText(desc_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap, elided_desc)

        # Draw Footer (Stacking bottom-up Phase 44)
        meta_font = QFont("IBM Plex Mono", 7)
        painter.setFont(meta_font)
        
        # 1. Created Date (Always Bottom)
        if note.created_at:
             try:
                 from datetime import datetime
                 dt = datetime.fromisoformat(note.created_at)
                 created_str = "Created: " + dt.strftime("%b %d, %I:%M %p")
                 painter.setPen(sub_text_color)
                 r = QRectF(text_rect.x(), content_rect.bottom() - 12, text_rect.width(), 12)
                 painter.drawText(r, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, created_str)
             except: pass

        # 2. Last Opened (Middle)
        if getattr(note, 'last_opened', None):
             try:
                 from datetime import datetime
                 dt = datetime.fromisoformat(note.last_opened)
                 opened_str = "Opened: " + dt.strftime("%b %d, %I:%M %p")
                 painter.setPen(sub_text_color)
                 r = QRectF(text_rect.x(), content_rect.bottom() - 24, text_rect.width(), 12)
                 painter.drawText(r, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, opened_str)
             except: pass
        
        # 3. Closed Date (Top)
        if is_closed:
             try:
                 from datetime import datetime
                 dt = datetime.now() # Fallback
                 if note.closed_at:
                     dt = datetime.fromisoformat(note.closed_at)
                 closed_str = "Closed: " + dt.strftime("%b %d, %I:%M %p")
                 painter.setPen(QColor("#10b981") if is_dark else QColor("#059669"))
                 r = QRectF(text_rect.x(), content_rect.bottom() - 36, text_rect.width(), 12)
                 painter.drawText(r, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, closed_str)
             except: pass

        # 4. Trash Original Location (Special)
        orig_folder = getattr(note, 'trash_original_folder_name', None)
        if orig_folder:
            painter.setFont(QFont("Inter", 7, QFont.Weight.Bold))
            painter.setPen(QColor("#ef4444") if is_dark else QColor("#b91c1c")) # Muted red
            
            # Draw tiny trash icon + folder name
            trash_icon = get_premium_icon("trash", color=painter.pen().color().name()).pixmap(10, 10)
            icon_x = text_rect.x()
            icon_y = content_rect.bottom() - 48 if is_closed else content_rect.bottom() - 36
            
            painter.drawPixmap(QPointF(icon_x, icon_y + 1), trash_icon)
            
            r = QRectF(icon_x + 14, icon_y, text_rect.width() - 14, 12)
            painter.drawText(r, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, f"Originally in: {orig_folder}")

        painter.restore()

    def editorEvent(self, event, model, option, index):
        if event.type() == event.Type.MouseButtonRelease:
            # Check if clicked inside cb_rect
            # We need to calculate cb_rect here again because paint() might not have been called recently
            # or we don't want to rely on the side effect of self.cb_rect.
            rect = option.rect
            card_rect = rect.adjusted(6, 4, -6, -4)
            cb_size = 18
            cb_padding = 10
            cb_rect = QRectF(card_rect.right() - cb_size - cb_padding, card_rect.top() + cb_padding, cb_size, cb_size)
            
            if cb_rect.contains(QPointF(event.position())):
                note = index.data(Qt.ItemDataRole.UserRole + 1)
                if note:
                    from datetime import datetime
                    is_currently_closed = bool(getattr(note, 'closed_at', None))
                    
                    updates = {}
                    if is_currently_closed:
                        updates['closed_at'] = None
                        updates['is_locked'] = False
                    else:
                        updates['closed_at'] = datetime.now().isoformat(timespec='microseconds')
                        updates['is_locked'] = True
                    
                    # We need to trigger an update. NoteList usually listens to signals.
                    # But delegates don't have easy access to NoteList signals.
                    # However, option.widget is the ListWidget.
                    # We can use the model to set data or call a method on the parent.
                    if option.widget:
                        # Parent of ListWidget is (usually) NoteList
                        parent = option.widget.parent()
                        while parent and not hasattr(parent, 'updateNote'):
                            parent = parent.parent()
                        
                        if parent and hasattr(parent, 'updateNote'):
                            parent.updateNote.emit(note.id, updates)
                            return True
        
        return super().editorEvent(event, model, option, index)
