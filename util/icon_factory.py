import base64
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtCore import QSize, QByteArray, QRectF
from util.icon_paths import ICONS

class IconFactory:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(IconFactory, cls).__new__(cls)
        return cls._instance

    def get_icon(self, name, color=None, size=QSize(24, 24)):
        """
        Returns a QIcon from the SVG path library.
        If color is provided, it replaces 'currentColor' in the SVG.
        """
        svg_data = ICONS.get(name)
        if not svg_data:
            # Fallback for missing icons
            return QIcon()

        if color:
            # If color is a QColor, convert to hex
            if isinstance(color, QColor):
                color_hex = color.name()
            else:
                color_hex = str(color)
            
            # Simple color injection
            svg_data = svg_data.replace('currentColor', color_hex)
            
        byte_array = QByteArray(svg_data.encode('utf-8'))
        renderer = QSvgRenderer(byte_array)
        
        pixmap = QPixmap(size)
        pixmap.fill(QColor(0, 0, 0, 0)) # Transparent
        
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        
        return QIcon(pixmap)

    def get_pixmap(self, name, color=None, size=QSize(24, 24)):
        """Utility for widgets that need QPixmap directly."""
        icon = self.get_icon(name, color, size)
        return icon.pixmap(size)

    def get_combined_indicators(self, names, color=None, size=QSize(14, 14), spacing=2):
        """
        Combines multiple icons into a single horizontal strip.
        Useful for showing Pin + Lock side-by-side in a native QListWidgetItem.
        """
        if not names:
            return QIcon()
        
        # Calculate combined width
        total_width = (size.width() * len(names)) + (spacing * (len(names) - 1))
        combined_pixmap = QPixmap(total_width, size.height())
        combined_pixmap.fill(QColor(0, 0, 0, 0))
        
        painter = QPainter(combined_pixmap)
        x_offset = 0
        for name in names:
            svg_data = ICONS.get(name)
            if svg_data:
                if color:
                    c_hex = color.name() if isinstance(color, QColor) else str(color)
                    svg_data = svg_data.replace('currentColor', c_hex)
                
                byte_array = QByteArray(svg_data.encode('utf-8'))
                renderer = QSvgRenderer(byte_array)
                renderer.render(painter, QRectF(x_offset, 0, size.width(), size.height()))
            
            x_offset += size.width() + spacing
        
        painter.end()
        return QIcon(combined_pixmap)

# Global helpers
def get_premium_icon(name, color=None, size=QSize(24, 24)):
    return IconFactory().get_icon(name, color, size)

def get_combined_indicators(names, color=None, size=QSize(14, 14), spacing=2):
    return IconFactory().get_combined_indicators(names, color, size, spacing)
