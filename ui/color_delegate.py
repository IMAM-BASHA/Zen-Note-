from PyQt6.QtWidgets import QStyledItemDelegate, QStyle, QListWidget
from PyQt6.QtGui import QColor, QPalette, QBrush, QPainter, QIcon, QPen
from PyQt6.QtCore import Qt, QRect, QSize
import ui.styles as styles

# Define a custom role for the color
COLOR_ROLE = Qt.ItemDataRole.UserRole + 10

class ColorDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme_mode = "light"

    def set_theme_mode(self, mode):
        self.theme_mode = mode

    def sizeHint(self, option, index):
        # Retrieve custom color to verify if we handle it
        # Strip whitespace to prevent invisible newlines from affecting size
        text = index.data(Qt.ItemDataRole.DisplayRole)
        if text: text = text.strip()
            
        # Standard size calculation with wrap support

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
            
        font = option.font
        font_metrics = option.fontMetrics
        # Calculate bounding rect with WordWrap
        rect = font_metrics.boundingRect(0, 0, width, 9999, 
                                        Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap, 
                                        text)
        
        # Add padding (Reduced to 8px top/bottom for compact card look)
        # Consistent height for all items
        height = max(36, rect.height() + 12) 
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
        
        # 1. Draw Background (Card Style for ALL items)
        
        # Default Card Background from Theme
        c = styles.ZEN_THEME.get(self.theme_mode, styles.ZEN_THEME["light"])
        
        # Determine background color
        if color and color.isValid():
            bg_color = color
            # If colored, use luminance for text
            luminance = (0.299 * color.red() + 0.587 * color.green() + 0.114 * color.blue()) / 255
            text_color = Qt.GlobalColor.white if luminance < 0.5 else Qt.GlobalColor.black
        else:
            # Uncolored = Default Card Style
            # Use 'card' color from theme (usually white or dark grey)
            bg_color = QColor(c.get('card', '#FFFFFF'))
            # Use theme foreground for text
            text_color = QColor(c.get('foreground', '#000000'))

        # Handle Selection Overlay/Border
        if is_selected:
             # Use Primary color for border
             primary_color = c['primary']
             painter.setPen(QPen(QColor(primary_color), 2))
             
             # If uncolored, maybe change background slightly?
             if not (color and color.isValid()):
                 bg_color = QColor(c.get('selection_bg', c['secondary']))
                 # Text color adjustment for selection?
                 # Zen theme typically uses Primary for selected text, but here we want contrast.
                 # Let's keep text_color as is (Foreground) or Primary?
                 # If bg is active_item_bg (light tint), foreground is fine.
        else:
             painter.setPen(Qt.PenStyle.NoPen)

        painter.setBrush(QBrush(bg_color))
        
        # Draw Rounded Rect (Adjusted for margin)
        # We want a card look, so let's add a small margin between items visually if needed, 
        # or just fill the styled rect. 
        # The QListWidget stylesheet sets margin-bottom, so option.rect might include that?
        # Typically option.rect is the allocation.
        # Let's draw slight indent.
        
        draw_rect = bg_rect
        if is_selected:
             draw_rect = bg_rect.adjusted(1, 1, -1, -1) # Inset for border
        
        painter.drawRoundedRect(draw_rect, 6, 6) # 6px radius for cards

        painter.setPen(text_color)
        
        # Font Styling (Title Hierarchy)
        font = option.font
        # REMOVED: Manually increasing font size caused jitter/jumps.
        # We rely on the font set by the stylesheet now.
        
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
        if text: text = text.strip()
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter | Qt.TextFlag.TextWordWrap, text)
                 
        painter.restore()
