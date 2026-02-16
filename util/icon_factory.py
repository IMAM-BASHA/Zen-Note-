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

    def get_icon(self, name, color=None, size=QSize(24, 24), glow=False, thick=False):
        """
        Returns a QIcon from the SVG path library.
        If color is provided, it replaces 'currentColor' in the SVG.
        If glow is True, it adds a soft light effect behind the icon.
        """
        svg_data = ICONS.get(name)
        if not svg_data:
            return QIcon()

        color_hex = "#FFFFFF"
        if color:
            if isinstance(color, QColor):
                color_hex = color.name()
            else:
                color_hex = str(color)
            svg_data = svg_data.replace('currentColor', color_hex)
        else:
            # Default to white if no color provided, for premium dark visibility
            svg_data = svg_data.replace('currentColor', "#FFFFFF")

        byte_array = QByteArray(svg_data.encode('utf-8'))
        renderer = QSvgRenderer(byte_array)
        
        pixmap = QPixmap(size)
        pixmap.fill(QColor(0, 0, 0, 0))
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        glow_rect = QRectF(0, 0, size.width(), size.height()).adjusted(0.5, 0.5, -0.5, -0.5)

        if glow:
            # 1. RENDER GLOW PASS
            # We render a white/light glow regardless of icon color for that "halo" effect
            byte_array_glow = QByteArray(svg_data.replace(color_hex, "#FFFFFF").encode('utf-8'))
            renderer_glow = QSvgRenderer(byte_array_glow)
            
            painter.setOpacity(0.4) # Slightly stronger glow
            offsets = [(-0.5, 0), (0.5, 0), (0, -0.5), (0, 0.5)]
            for dx, dy in offsets:
                renderer_glow.render(painter, glow_rect.translated(dx, dy))
            
            painter.setOpacity(1.0)
            
        # 1.5 RENDER THICKNESS PASS (Fake Bold)
        if thick:
            # Render "stroke" by drawing the icon itself at offsets
            # Use slightly lower opacity to blend smoothly
            painter.setOpacity(0.5)
            # Use 0.5px offsets for a smoother, less distorted bold effect
            stroke_offsets = [
                (-0.5, 0), (0.5, 0), (0, -0.5), (0, 0.5),
                (-0.35, -0.35), (0.35, -0.35), (-0.35, 0.35), (0.35, 0.35)
            ]
            for dx, dy in stroke_offsets:
                renderer.render(painter, glow_rect.translated(dx, dy))
            painter.setOpacity(1.0)

        # 2. RENDER MAIN ICON
        renderer.render(painter)
        painter.end()
        
        return QIcon(pixmap)

    def get_pixmap(self, name, color=None, size=QSize(24, 24), glow=False, thick=False):
        """Utility for widgets that need QPixmap directly."""
        icon = self.get_icon(name, color, size, glow=glow, thick=thick)
        return icon.pixmap(size)

    def get_combined_indicators(self, names, color=None, size=QSize(14, 14), spacing=2, glow=False):
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
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        x_offset = 0
        for name in names:
            svg_data = ICONS.get(name)
            if svg_data:
                c_hex = "#FFFFFF"
                if color:
                    c_hex = color.name() if isinstance(color, QColor) else str(color)
                svg_data = svg_data.replace('currentColor', c_hex)
                
                byte_array = QByteArray(svg_data.encode('utf-8'))
                renderer = QSvgRenderer(byte_array)
                
                rect = QRectF(x_offset, 0, size.width(), size.height())
                
                if glow:
                    # RENDER GLOW PASS
                    byte_array_glow = QByteArray(svg_data.replace(c_hex, "#FFFFFF").encode('utf-8'))
                    renderer_glow = QSvgRenderer(byte_array_glow)
                    
                    painter.setOpacity(0.4)
                    offsets = [(-0.5, 0), (0.5, 0), (0, -0.5), (0, 0.5)]
                    for dx, dy in offsets:
                        renderer_glow.render(painter, rect.translated(dx, dy))
                    painter.setOpacity(1.0)

                renderer.render(painter, rect)
            
            x_offset += size.width() + spacing
        
        painter.end()
        return QIcon(combined_pixmap)

# Global helpers
def get_premium_icon(name, color=None, size=QSize(24, 24), glow=True, thick=False):
    # We enable glow by default for the 'premium' look requested
    return IconFactory().get_icon(name, color, size, glow=glow, thick=thick)

def get_combined_indicators(names, color=None, size=QSize(14, 14), spacing=2, glow=True):
    return IconFactory().get_combined_indicators(names, color, size, spacing, glow=glow)
