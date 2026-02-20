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
            # Calculate width based on viewport but cap it for Zen look
            # Cards shouldn't be too wide in List view to maintain readability
            width = list_widget.viewport().width() - 12 # Padding buffer
            width = min(400, width) # Cap card width
        else:
            width = min(400, option.rect.width() - 12)
            
        if width < 50: width = 200 # Fallback
            
        font = option.font
        font_metrics = option.fontMetrics
        # Calculate bounding rect with WordWrap
        # Fixed stable height for List View items (Card Style)
        # Reduced from 54 to 40 for a tighter, more typical list look instead of oversized cards
        return QSize(int(width), 40)

    def paint(self, painter, option, index):
        painter.save()
        
        # Retrieve custom color
        color_data = index.data(COLOR_ROLE)
        color = QColor(color_data) if color_data else None

        # Determine if selected
        is_selected = option.state & QStyle.StateFlag.State_Selected
        if is_selected:
            pass # print(f"DEBUG: ColorDelegate Painting SELECTED item: {index.row()} | Palette Highlight: {option.palette.highlight().color().name()}")
        
        # Standardize rect with proper margins for the "Card" look
        rect = option.rect
        
        # Consistent width cap for List mode cards (Avoid excessive stretching)
        # Left-aligned for a more standard/anchored list feel as requested
        card_w = min(400, rect.width() - 12)
        # Reduced internal vertical margin to decrease padded look
        bg_rect = QRect(rect.left() + 6, rect.top() + 2, card_w, rect.height() - 4)
        
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
             # Use subtle border color from theme for non-selected items
             painter.setPen(QPen(QColor(c.get('border', '#E0DDD9')), 1))

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
        
        painter.drawRoundedRect(draw_rect, 8, 8) # 8px radius for cleaner cards
        painter.setPen(text_color)
        
        # Font Styling (Title Hierarchy)
        font = option.font
        
        if is_selected:
            font.setBold(True)
            font.setWeight(700) # Extra bold for selection
        
        painter.setFont(font)
        
        # 2. Draw Icon
        icon = index.data(Qt.ItemDataRole.DecorationRole)
        if icon and isinstance(icon, QIcon):
            icon_size = option.decorationSize
            icon_y = rect.top() + (rect.height() - icon_size.height()) // 2
            # Position icon inside the card (bg_rect.left() + padding)
            icon_rect = QRect(bg_rect.left() + 10, icon_y, icon_size.width(), icon_size.height())
            icon.paint(painter, icon_rect, Qt.AlignmentFlag.AlignCenter, 
                       QIcon.Mode.Selected if is_selected else QIcon.Mode.Normal, QIcon.State.On)
            text_x = icon_rect.right() + 12
        else:
            text_x = bg_rect.left() + 10


        # 3. Draw Text with Elision ("...")
        # Capping note title to a single line for a clean list look
        # Strict padding: 10px from card edge
        text_rect = QRect(text_x, rect.top(), bg_rect.right() - text_x - 10, rect.height())
        text = index.data(Qt.ItemDataRole.DisplayRole)
        if text: 
            text = text.strip().replace('\n', ' ') # Clean up newlines for list view
            elided_text = painter.fontMetrics().elidedText(text, Qt.TextElideMode.ElideRight, text_rect.width())
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, elided_text)
                 
        painter.restore()
