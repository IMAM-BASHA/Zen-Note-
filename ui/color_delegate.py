from PyQt6.QtWidgets import QStyledItemDelegate, QStyle, QListWidget
from PyQt6.QtGui import QColor, QPalette, QBrush, QPainter, QIcon
from PyQt6.QtCore import Qt, QRect, QSize

# Define a custom role for the color
COLOR_ROLE = Qt.ItemDataRole.UserRole + 10

class ColorDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def sizeHint(self, option, index):
        # Retrieve custom color to verify if we handle it
        color_data = index.data(COLOR_ROLE)
        if not color_data:
            return super().sizeHint(option, index)
            
        # Standard size calculation with wrap support
        text = index.data(Qt.ItemDataRole.DisplayRole)
        icon = index.data(Qt.ItemDataRole.DecorationRole)
        
        # Determine available width for text
        # List width - scrollbar - margins - icon
        list_widget = self.parent()
        if isinstance(list_widget, QListWidget):
            width = list_widget.viewport().width() - 30 # Margin buffer
            if icon:
                width -= (option.decorationSize.width() + 10)
        else:
            width = option.rect.width() - 40
            
        if width < 50: width = 200 # Fallback
            
        font_metrics = option.fontMetrics
        # Calculate bounding rect with WordWrap
        rect = font_metrics.boundingRect(0, 0, width, 9999, 
                                        Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap, 
                                        text)
        
        # Add padding (12px top + 12px bottom + small buffer)
        height = max(32, rect.height() + 16)
        return QSize(width, height)

    def paint(self, painter, option, index):
        painter.save()
        
        # Retrieve custom color
        color_data = index.data(COLOR_ROLE)
        color = QColor(color_data) if color_data else None

        # Determine if selected
        is_selected = option.state & QStyle.StateFlag.State_Selected
        if is_selected:
            pass # print(f"DEBUG: ColorDelegate Painting SELECTED item: {index.row()} | Palette Highlight: {option.palette.highlight().color().name()}")
        
        # Standardize rect with padding
        rect = option.rect
        bg_rect = rect.adjusted(2, 1, -2, -1)
        
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        
        # 1. Draw Background
        if color and color.isValid():
            # ... (Logic for custom colors remains same) ...
            if is_selected:
                bg_color = color
                # Fix Highlighting: Make color slightly brighter/darker to show selection? 
                # Or just keep it flat but ensure text contrast.
                # Actually, if custom color is set, we use it as background.
                # To show selection, we might add a border or darken it?
                # For now, simplistic approach:
                luminance = (0.299 * color.red() + 0.587 * color.green() + 0.114 * color.blue()) / 255
                text_color = Qt.GlobalColor.white if luminance < 0.5 else Qt.GlobalColor.black
            else:
                bg_color = QColor(color)
                bg_color.setAlphaF(0.25)
                text_color = option.palette.text().color()
            
            painter.setBrush(QBrush(bg_color))
            painter.drawRoundedRect(bg_rect, 4, 4)
        else:
            # Standard Item (No Custom Color)
            if is_selected:
                # Use the palette's highlight set by Stylesheet
                bg_brush = option.palette.highlight()
                
                # Draw Selection Background
                painter.setBrush(bg_brush)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(bg_rect, 4, 4)
                
                # Use Palette HighlightedText color (matches Zen Theme)
                text_color = option.palette.highlightedText().color()

                # Draw subtle border if needed (from style or manually)
                # For Zen, we have a border in CSS, but delegate might hide it if we don't draw it.
                # Actually, QListWidget selection border is handled by CSS if we don't clear it.
                # But here we are painting.
                # Let's draw a border using the PRIMARY color found in palette link or hardcoded logic?
                # Stylesheet sets: border: 1px solid {c['primary']}
                # We can try to access it via option.palette.link().color() if we mapped it, 
                # but standard palette doesn't map 'primary' reliably.
                # We'll trust the background fill is sufficient or use a generic border.
                
            else:
                text_color = option.palette.text().color()

        painter.setPen(text_color)
        
        # Font Styling (Title Hierarchy)
        font = option.font
        # Fix: handle pointSize() returning -1 (if size is in pixels)
        ps = font.pointSize()
        if ps > 0:
            font.setPointSize(ps + 1) 
        elif font.pixelSize() > 0:
            font.setPixelSize(font.pixelSize() + 1)
        
        if is_selected:
            font.setBold(True)
            font.setWeight(700) # Extra bold for selection
        
        painter.setFont(font)
        
        # 2. Draw Icon
        icon = index.data(Qt.ItemDataRole.DecorationRole)
        text_x = rect.left() + 8
        if icon and isinstance(icon, QIcon):
            icon_size = option.decorationSize
            icon_y = rect.top() + (rect.height() - icon_size.height()) // 2
            icon_rect = QRect(rect.left() + 6, icon_y, icon_size.width(), icon_size.height())
            icon.paint(painter, icon_rect, Qt.AlignmentFlag.AlignCenter, 
                       QIcon.Mode.Selected if is_selected else QIcon.Mode.Normal, QIcon.State.On)
            text_x = icon_rect.right() + 8

        # 3. Draw Text with Word Wrap
        text_rect = QRect(text_x, rect.top() + 4, rect.right() - text_x - 6, rect.height() - 8)
        text = index.data(Qt.ItemDataRole.DisplayRole)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter | Qt.TextFlag.TextWordWrap, text)
                 
        painter.restore()
