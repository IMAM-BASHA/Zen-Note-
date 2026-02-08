"""
Professional Scrble Ink - Industry-Level Digital Whiteboard
Advanced features: shapes, images, professional tools, themes, advanced eraser
"""

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QToolBar, 
                               QLabel, QSlider, QColorDialog, QFileDialog, QMessageBox,
                               QMenu, QWidgetAction, QVBoxLayout, QHBoxLayout, QPushButton,
                               QSpinBox, QComboBox, QDialog, QDialogButtonBox, QCheckBox,
                               QScrollArea, QFrame, QStatusBar)
from PyQt6.QtCore import Qt, QPointF, QRectF, QLineF, pyqtSignal, QPoint, QSize, QSettings, QEvent, QSizeF, QRect
from PyQt6.QtGui import (QPainter, QPen, QColor, QPainterPath, QAction, 
                          QIcon, QPixmap, QTabletEvent, QMouseEvent, QPaintEvent,
                          QImage, QBrush, QLinearGradient, QRadialGradient, 
                          QPainterPathStroker, QPalette, QPointingDevice, QCursor, QActionGroup,
                          QPolygonF)
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Any
from enum import Enum
import sys
import json
import math
import time



class ThemeConfig:
    """Centralized Theme Configuration"""
    # Colors
    BG_DARK = "#1E1E1E"
    BG_DARKER = "#121212"
    BG_LIGHT = "#2D2D2D"
    ACCENT = "#00ADB5"  # Teal
    ACCENT_HOVER = "#00D2DC"
    ACCENT_PRESSED = "#008C94"
    TEXT_PRIMARY = "#EEEEEE"
    TEXT_SECONDARY = "#AAAAAA"
    BORDER = "rgba(255, 255, 255, 0.1)"
    GLASS = "rgba(45, 45, 45, 0.7)"
    
    # Fonts
    FONT_FAMILY = "Segoe UI"
    FONT_SIZE_MAIN = 8
    FONT_SIZE_HEADER = 11
    
    # Dimensions
    RADIUS = 4
    PADDING = 4

class ModernButton(QPushButton):
    """Premium Styled Button"""
    def __init__(self, text="", parent=None, is_primary=False):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.is_primary = is_primary
        self.setFixedHeight(24)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Determine colors
        if self.is_primary:
            bg_color = QColor(ThemeConfig.ACCENT)
            text_color = QColor(ThemeConfig.BG_DARKER)
            border_color = QColor(ThemeConfig.ACCENT)
        else:
            bg_color = QColor(ThemeConfig.BG_LIGHT)
            text_color = QColor(ThemeConfig.TEXT_PRIMARY)
            border_color = QColor(255, 255, 255, 30)
            
        if self.isDown():
            bg_color = bg_color.darker(110)
        elif self.underMouse():
            bg_color = bg_color.lighter(110)
            
        # Draw background
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), ThemeConfig.RADIUS, ThemeConfig.RADIUS)
        painter.fillPath(path, bg_color)
        
        # Draw border
        pen = QPen(border_color, 1)
        painter.setPen(pen)
        painter.drawPath(path)
        
        # Draw text
        painter.setPen(text_color)
        font = self.font()
        font.setFamily(ThemeConfig.FONT_FAMILY)
        font.setBold(True if self.is_primary else False)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.text())

class ModernDialog(QDialog):
    """Base class for modern frameless dialogs"""
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(400, 200)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Main container with glass effect
        self.container = QFrame()
        self.container.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeConfig.BG_DARK};
                border: 1px solid {ThemeConfig.BORDER};
                border-radius: {ThemeConfig.RADIUS}px;
            }}
        """)
        
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(20, 10, 20, 20)
        
        # Title bar
        title_bar = QHBoxLayout()
        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {ThemeConfig.TEXT_PRIMARY}; font-size: {ThemeConfig.FONT_SIZE_HEADER}pt; font-weight: bold; border: none;")
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.reject)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                color: {ThemeConfig.TEXT_SECONDARY};
                background: transparent;
                border: none;
                font-size: 14pt;
            }}
            QPushButton:hover {{ color: {ThemeConfig.ACCENT}; }}
        """)
        
        title_bar.addWidget(title_label)
        title_bar.addStretch()
        title_bar.addWidget(close_btn)
        
        container_layout.addLayout(title_bar)
        
        # Content area
        self.content_area = QVBoxLayout()
        container_layout.addLayout(self.content_area)
        
        layout.addWidget(self.container)
        
        # Dragging logic
        self.old_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.old_pos:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.pos() + delta)
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.old_pos = None

    def paintEvent(self, event):
        # Drop shadow
        pass

class ModernMessageBox(ModernDialog):
    """Custom Message Box"""
    def __init__(self, title, message, buttons=QMessageBox.StandardButton.Ok, parent=None):
        super().__init__(title, parent)
        
        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        msg_label.setStyleSheet(f"color: {ThemeConfig.TEXT_PRIMARY}; font-size: 11pt; border: none;")
        self.content_area.addWidget(msg_label)
        
        self.content_area.addSpacing(20)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        if buttons & QMessageBox.StandardButton.Yes:
            yes_btn = ModernButton("Yes", is_primary=True)
            yes_btn.clicked.connect(self.accept)
            btn_layout.addWidget(yes_btn)
            
        if buttons & QMessageBox.StandardButton.No:
            no_btn = ModernButton("No")
            no_btn.clicked.connect(self.reject)
            btn_layout.addWidget(no_btn)
            
        if buttons & QMessageBox.StandardButton.Ok:
            ok_btn = ModernButton("OK", is_primary=True)
            ok_btn.clicked.connect(self.accept)
            btn_layout.addWidget(ok_btn)
            
        self.content_area.addLayout(btn_layout)

class ToolType(Enum):
    PEN = "pen"
    BALLPOINT = "ballpoint"
    MARKER = "marker"
    PENCIL = "pencil"
    HIGHLIGHTER = "highlighter"
    ERASER = "eraser"
    STROKE_ERASER = "stroke_eraser"
    SELECT = "select"

    LINE = "line"
    RECTANGLE = "rectangle"
    CIRCLE = "circle"
    ARROW = "arrow"
    DOUBLE_ARROW = "double_arrow"
    TEXT = "text"


class BackgroundType(Enum):
    DOTS = "dots"
    GRID = "grid"
    LINES = "lines"
    LINES_URL_PAPER = "lines_url" # Renamed to avoid confusion if needed, but keeping simple
    LINES_WITH_MARGIN = "lines_with_margin"
    PLAIN = "plain"
    GRAPH = "graph"


class UndoType(Enum):
    ADD_STROKE = 1
    ERASE_STROKES = 2
    ADD_SHAPE = 3
    CLEAR = 4
    ADD_IMAGE = 5


@dataclass
class UndoAction:
    action_type: UndoType
    data: Any  # Depends on action_type
    # For ERASE: List[Tuple[int, Any]]  # (index, stroke_obj)
    # For ADD: The object itself



@dataclass
class Stroke:
    """Represents a single ink stroke with advanced properties"""
    points: List[Tuple[float, float, float]] = field(default_factory=list)  # x, y, pressure
    color: QColor = field(default_factory=lambda: QColor(255, 255, 255))
    width: float = 3.0
    tool: ToolType = ToolType.PEN
    opacity: float = 1.0
    smoothness: int = 2  # Smoothing level
    is_deleted: bool = False
    
    # Cache for path optimization
    _path: Any = field(default=None, init=False, repr=False)
    _smoothed_points: Any = field(default=None, init=False, repr=False)
    
    @property
    def path(self) -> QPainterPath:
        """Get or calculate QPainterPath with caching."""
        if self._path is not None:
            return self._path
            
        path = QPainterPath()
        if not self.points:
            self._path = path
            return path
            
        # Get smoothed points if needed
        # We reuse the logic from the canvas but cache it here
        points = self.get_smoothed_points()
        
        if len(points) < 2:
            self._path = path
            return path
            
        path.moveTo(points[0][0], points[0][1])
        
        # Use quadratic curves for smoother lines
        for i in range(1, len(points)):
            if i < len(points) - 1:
                # Calculate control point
                c_x = (points[i][0] + points[i+1][0]) / 2
                c_y = (points[i][1] + points[i+1][1]) / 2
                path.quadTo(points[i][0], points[i][1], c_x, c_y)
            else:
                path.lineTo(points[i][0], points[i][1])
            
        self._path = path
        return path
        
    def get_smoothed_points(self) -> List[Tuple[float, float, float]]:
        """Calculate and cache smoothed points."""
        if self._smoothed_points is not None:
            return self._smoothed_points
            
        if self.smoothness == 0 or len(self.points) < 3:
            self._smoothed_points = self.points
            return self.points
            
        smoothed = []
        window = min(self.smoothness * 2 + 1, len(self.points))
        
        for i in range(len(self.points)):
            start = max(0, i - window // 2)
            end = min(len(self.points), i + window // 2 + 1)
            
            avg_x = sum(p[0] for p in self.points[start:end]) / (end - start)
            avg_y = sum(p[1] for p in self.points[start:end]) / (end - start)
            pressure = self.points[i][2]
            
            smoothed.append((avg_x, avg_y, pressure))
            
        self._smoothed_points = smoothed
        return smoothed

    def invalidate_path(self):
        """Force recalculation of path and smoothed points."""
        self._path = None
        self._smoothed_points = None
    
    def to_dict(self):
        return {
            'points': self.points,
            'color': self.color.name(),
            'width': self.width,
            'tool': self.tool.value,
            'opacity': self.opacity,
            'smoothness': self.smoothness
        }
    
    @staticmethod
    def from_dict(data):
        stroke = Stroke()
        stroke.points = data['points']
        stroke.color = QColor(data['color'])
        stroke.width = data['width']
        stroke.tool = ToolType(data['tool'])
        stroke.opacity = data.get('opacity', 1.0)
        stroke.smoothness = data.get('smoothness', 2)
        return stroke


@dataclass
class ShapeObject:
    """Represents geometric shapes"""
    shape_type: ToolType
    start: QPointF
    end: QPointF
    color: QColor
    width: float
    
    def to_dict(self):
        return {
            'shape_type': self.shape_type.value,
            'start': (self.start.x(), self.start.y()),
            'end': (self.end.x(), self.end.y()),
            'color': self.color.name(),
            'width': self.width
        }
    
    @staticmethod
    def from_dict(data):
        return ShapeObject(
            shape_type=ToolType(data['shape_type']),
            start=QPointF(*data['start']),
            end=QPointF(*data['end']),
            color=QColor(data['color']),
            width=data['width']
        )


@dataclass
class ImageObject:
    """Represents an image on canvas"""
    image: QImage
    position: QPointF
    size: QSize
    
    def to_dict(self):
        # Convert image to base64 for saving
        from PyQt6.QtCore import QBuffer, QByteArray, QIODevice
        import base64
        
        ba = QByteArray()
        buffer = QBuffer(ba)
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        success = self.image.save(buffer, "PNG")
        if not success:
            print("Failed to save image to buffer")
            return None
            
        img_str = base64.b64encode(ba.data()).decode('utf-8')
        
        return {
            'image_data': img_str,
            'position': (self.position.x(), self.position.y()),
            'size': (self.size.width(), self.size.height())
        }
    
    @staticmethod
    def from_dict(data):
        import base64
        from PyQt6.QtCore import QByteArray
        
        if not data or 'image_data' not in data:
            return None
            
        try:
            img_data = base64.b64decode(data['image_data'])
            ba = QByteArray(img_data)
            image = QImage()
            if not image.loadFromData(ba, "PNG"):
                # Try auto-detect if PNG fails
                if not image.loadFromData(ba):
                    print("Failed to load image from data")
                    return None
            
            return ImageObject(
                image=image,
                position=QPointF(*data['position']),
                size=QSize(int(data['size'][0]), int(data['size'][1]))
            )
        except Exception as e:
            print(f"Error loading image: {e}")
            return None


@dataclass
class Page:
    """Represents a single page/canvas with all content"""
    name: str = "Untitled"
    section: str = "" # NEW: Grouping header (e.g. Note Title)
    strokes: List[Stroke] = field(default_factory=list)
    shapes: List[ShapeObject] = field(default_factory=list)
    images: List[ImageObject] = field(default_factory=list)
    undone_strokes: List[Stroke] = field(default_factory=list)
    undone_shapes: List[ShapeObject] = field(default_factory=list)
    background_type: BackgroundType = BackgroundType.DOTS
    background_color: QColor = field(default_factory=lambda: QColor(30, 30, 30))
    
    def to_dict(self):
        return {
            'name': self.name,
            'section': self.section,
            'strokes': [s.to_dict() for s in self.strokes],
            'shapes': [s.to_dict() for s in self.shapes],
            'images': [i.to_dict() for i in self.images],
            'background_type': self.background_type.value,
            'background_color': self.background_color.name()
        }
    
    @staticmethod
    def from_dict(data):
        page = Page(name=data['name'])
        page.section = data.get('section', "")
        page.strokes = [Stroke.from_dict(s) for s in data['strokes']]
        page.shapes = [ShapeObject.from_dict(s) for s in data.get('shapes', [])]
        page.images = [ImageObject.from_dict(i) for i in data.get('images', [])]
        page.background_type = BackgroundType(data.get('background_type', 'dots'))
        page.background_color = QColor(data.get('background_color', '#1e1e1e'))
        return page


class InkCanvas(QWidget):
    """Professional drawing canvas with advanced features"""
    
    stroke_added = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(200, 200)
        self.setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_TabletTracking, True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Drawing state
        self.current_stroke: Optional[Stroke] = None
        self.current_shape: Optional[ShapeObject] = None
        self.shape_start: Optional[QPointF] = None
        
        # Selection state
        self.selection_active = False
        self.selection_rect: Optional[QRectF] = None
        self.selection_start: Optional[QPointF] = None
        self.selected_strokes: List[int] = []
        self.selected_shapes: List[int] = []
        self.selected_images: List[int] = []
        self.is_moving_selection = False
        self.selection_offset = QPointF()
        
        # Resize state (for images and shapes)
        self.is_resizing = False
        self.resize_handle_idx = -1
        self.resize_original_rect = None
        self.resize_start_pos = None
        
        # Tool settings
        self.current_tool = ToolType.PEN
        self.current_color = QColor(255, 255, 255)
        self.pen_width = 3.0
        self.smoothing_level = 2
        
        # Pen type settings
        self.pen_styles = {
            ToolType.PEN: {'width': 3.0, 'opacity': 1.0, 'cap': Qt.PenCapStyle.RoundCap},
            ToolType.BALLPOINT: {'width': 2.0, 'opacity': 0.9, 'cap': Qt.PenCapStyle.RoundCap},
            ToolType.MARKER: {'width': 8.0, 'opacity': 0.7, 'cap': Qt.PenCapStyle.FlatCap},
            ToolType.PENCIL: {'width': 2.5, 'opacity': 0.6, 'cap': Qt.PenCapStyle.RoundCap},
            ToolType.HIGHLIGHTER: {'width': 20.0, 'opacity': 0.3, 'cap': Qt.PenCapStyle.FlatCap}
        }
        
        # Eraser settings
        self.eraser_width = 20.0
        self.stroke_eraser_mode = False
        
        # Current page data
        self.strokes: List[Stroke] = []
        self.shapes: List[ShapeObject] = []
        self.images: List[ImageObject] = []
        
        # Undo/Redo Stacks (Command Pattern)
        self.undo_stack: List[UndoAction] = []
        self.redo_stack: List[UndoAction] = []
        
        # Legacy lists (kept for compatibility if needed, but unused)
        self.undone_strokes: List[Stroke] = []
        self.undone_shapes: List[ShapeObject] = []
        
        # Background settings
        self.background_type = BackgroundType.DOTS
        self.background_color = QColor(30, 30, 30)
        self.grid_color = QColor(60, 60, 60)
        self.grid_spacing = 30
        
        
        # Zoom and pan
        self.zoom_level = 1.0
        self.pan_offset = QPointF(0, 0)
        self.is_panning = False
        self.last_pan_point = QPointF()
        
        
        # Region Selection (Crop/cut tool)
        self.region_rect = None  # Captured region rectangle
        
        # Resize state variables
        self.is_resizing = False
        self.resize_handle_idx = -1
        self.resize_original_rect = None
        self.resize_start_pos = None
        
        # Spatial Optimization
        self.spatial_grid = {}  # {grid_key: [stroke_indices]}
        self.grid_size = 100    # pixels per grid cell (tuned for typical stroke size)

        # Layer Caching (Performance)
        # Layer Caching (Performance)
        self.cached_pixmap: Optional[QPixmap] = None
        self.content_cache_valid = False
        self.region_clipboard = None  # Stored QImage of captured region
        
        # Eraser throttling
        self.last_eraser_time = 0
        
        # Performance: cache background
        self.background_cache: Optional[QPixmap] = None
        self.bg_cache_valid = False
        
        # Load saved settings
        self.load_settings()
        
        # Track if we're initializing (to avoid saving during __init__)
        self._initialized = True
    
    def __setattr__(self, name, value):
        """Override to auto-save when tool settings change"""
        super().__setattr__(name, value)
        
        # Update pen_styles when pen_width changes for the current tool
        if name == 'pen_width' and hasattr(self, 'current_tool') and hasattr(self, 'pen_styles'):
            if self.current_tool in self.pen_styles:
                self.pen_styles[self.current_tool]['width'] = value
        
        # Update pen_styles when eraser_width changes
        if name == 'eraser_width' and hasattr(self, 'pen_styles'):
            if ToolType.ERASER in self.pen_styles:
                self.pen_styles[ToolType.ERASER]['width'] = value
        
        # Only save if fully initialized and changing a settings property
        if hasattr(self, '_initialized') and name in [
            'current_tool', 'pen_width', 'eraser_width', 'current_color',
            'background_type', 'background_color', 'show_ruler', 'smoothing_level'
        ]:
            # Delay save to avoid excessive saves during rapid changes
            if hasattr(self, '_save_timer'):
                self._save_timer.stop()
            else:
                from PyQt6.QtCore import QTimer
                self._save_timer = QTimer()
                self._save_timer.setSingleShot(True)
                self._save_timer.timeout.connect(self.save_settings)
            self._save_timer.start(500)  # Save after 500ms of no changes
    
    def save_settings(self):
        """Save current tool settings to JSON file"""
        try:
            import os
            from enum import Enum
            settings_dir = os.path.expanduser("~/.whiteboard_settings")
            os.makedirs(settings_dir, exist_ok=True)
            settings_file = os.path.join(settings_dir, "preferences.json")
            
            # Helper to get value from enum or return as-is
            def get_value(obj):
                return obj.value if isinstance(obj, Enum) else obj
            
            settings = {
                'current_tool': get_value(self.current_tool),
                'current_color': self.current_color.name(),
                'pen_width': self.pen_width,
                'pen_styles': {
                    # Convert ToolType enum keys to their string values
                    get_value(tool): {'width': style['width'], 'opacity': style['opacity']}
                    for tool, style in self.pen_styles.items()
                },
                'eraser_width': self.eraser_width,
                'background_type': get_value(self.background_type),
                'background_color': self.background_color.name(),
                'grid_color': self.grid_color.name(),
                'grid_spacing': self.grid_spacing,

                'smoothing_level': self.smoothing_level
            }
            
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=2)

        except Exception as e:
            print(f"Error saving settings: {e}")
            import traceback
            traceback.print_exc()
    
    def load_settings(self):
        """Load tool settings from JSON file"""
        try:
            import os
            settings_file = os.path.join(os.path.expanduser("~/.whiteboard_settings"), "preferences.json")
            
            if not os.path.exists(settings_file):
                return  # Use defaults
            
            with open(settings_file, 'r') as f:
                settings = json.load(f)
            
            # Helper to find ToolType enum by value
            def get_tool_by_value(value, default):
                if value is None:
                    return default
                for tool in ToolType:
                    if tool.value == value:
                        return tool
                # Deprecated tool encountered (e.g., region_select)
                if value == 'region_select':
                    print(f"Warning: 'region_select' tool deprecated, defaulting to SELECT")
                    return ToolType.SELECT
                return default
            
            # Helper to find BackgroundType enum by value
            def get_bg_by_value(value, default):
                if value is None:
                    return default
                for bg in BackgroundType:
                    if bg.value == value:
                        return bg
                return default
            
            # Restore settings - convert string values back to enums
            self.current_tool = get_tool_by_value(settings.get('current_tool'), ToolType.PEN)
            self.current_color = QColor(settings.get('current_color', '#FFFFFF'))
            self.pen_width = settings.get('pen_width', 3.0)
            
            # Restore pen styles (convert string keys back to ToolType enums)
            saved_styles = settings.get('pen_styles', {})
            for tool_value, style_data in saved_styles.items():
                # Find the matching ToolType enum
                matching_tool = get_tool_by_value(tool_value, None)
                if matching_tool and matching_tool in self.pen_styles:
                    self.pen_styles[matching_tool]['width'] = style_data.get('width', self.pen_styles[matching_tool]['width'])
                    self.pen_styles[matching_tool]['opacity'] = style_data.get('opacity', self.pen_styles[matching_tool]['opacity'])
            
            self.eraser_width = settings.get('eraser_width', 20.0)
            self.background_type = get_bg_by_value(settings.get('background_type'), BackgroundType.DOTS)
            self.background_color = QColor(settings.get('background_color', '#1E1E1E'))
            self.grid_color = QColor(settings.get('grid_color', '#3C3C3C'))
            self.grid_spacing = settings.get('grid_spacing', 30)
            self.show_ruler = settings.get('show_ruler', False)
            self.smoothing_level = settings.get('smoothing_level', 2)
            
            # IMPORTANT: Sync pen_width with current_tool's saved width
            # This ensures the width slider shows the correct value for the selected tool
            if self.current_tool in self.pen_styles:
                self.pen_width = self.pen_styles[self.current_tool]['width']
            
        except Exception as e:
            print(f"Error loading settings: {e}")
    

    
    def load_page_data(self, page: Page):
        """Load page data into canvas"""
        self.strokes = list(page.strokes)
        self.shapes = list(page.shapes)
        self.images = list(page.images)
        self.undone_strokes = list(page.undone_strokes)
        self.undone_shapes = list(page.undone_shapes)
        self.background_type = page.background_type
        self.background_color = page.background_color
        self.rebuild_spatial_grid()
        self.bg_cache_valid = False
        self.content_cache_valid = False
        self.update()
    
    def save_page_data(self, page: Page):
        """Save canvas data back to page"""
        page.strokes = self.strokes
        page.shapes = self.shapes
        page.images = self.images
        page.undone_strokes = self.undone_strokes
        page.undone_shapes = self.undone_shapes
        page.background_type = self.background_type
        page.background_color = self.background_color
    
    def set_tool(self, tool: ToolType):
        self.current_tool = tool
        if tool in self.pen_styles:
            self.pen_width = self.pen_styles[tool]['width']
    
    def set_color(self, color: QColor):
        self.current_color = color
    
    def set_pen_width(self, width: float):
        self.pen_width = width
    
    def set_background_type(self, bg_type: BackgroundType):
        self.background_type = bg_type
        self.bg_cache_valid = False
        self.update()
    
    def set_background_color(self, color: QColor):
        self.background_color = color
        self.bg_cache_valid = False
        self.update()
    
    def add_image(self, image_path: str):
        """Add image to canvas with Undo support"""
        image = QImage(image_path)
        if not image.isNull():
            # Scale image if too large
            max_size = 800
            if image.width() > max_size or image.height() > max_size:
                image = image.scaled(max_size, max_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            
            img_obj = ImageObject(
                image=image,
                position=QPointF(100, 100),
                size=image.size()
            )
            self.images.append(img_obj)
            
            # Add to Undo Stack
            action = UndoAction(UndoType.ADD_IMAGE, img_obj)
            self.undo_stack.append(action)
            self.redo_stack.clear()
            
            self.content_cache_valid = False
            self.update()
    
    def undo(self):
        """Advanced Undo"""
        if not self.undo_stack:
            return
            
        action = self.undo_stack.pop()
        self.redo_stack.append(action)
        
        if action.action_type == UndoType.ADD_STROKE:
            if action.data in self.strokes:
                self.strokes.remove(action.data)
                
        elif action.action_type == UndoType.ERASE_STROKES:
            for index, stroke in sorted(action.data, key=lambda x: x[0]):
                if index <= len(self.strokes):
                    self.strokes.insert(index, stroke)
                else:
                    self.strokes.append(stroke)
                    
        elif action.action_type == UndoType.ADD_SHAPE:
            if action.data in self.shapes:
                self.shapes.remove(action.data)
                
        elif action.action_type == UndoType.ADD_IMAGE:
            if action.data in self.images:
                self.images.remove(action.data)
                
        elif action.action_type == UndoType.CLEAR:
            data = action.data
            self.strokes = list(data['strokes'])
            self.shapes = list(data['shapes'])
            self.images = list(data['images'])
                    
        self.rebuild_spatial_grid()
        self.content_cache_valid = False
        self.update()
    
    def redo(self):
        """Advanced Redo"""
        if not self.redo_stack:
            return
            
        action = self.redo_stack.pop()
        self.undo_stack.append(action)
        
        if action.action_type == UndoType.ADD_STROKE:
            self.strokes.append(action.data)
            
        elif action.action_type == UndoType.ERASE_STROKES:
            strokes_to_remove = [x[1] for x in action.data]
            self.strokes = [s for s in self.strokes if s not in strokes_to_remove]
            
        elif action.action_type == UndoType.ADD_SHAPE:
            self.shapes.append(action.data)
            
        elif action.action_type == UndoType.ADD_IMAGE:
            self.images.append(action.data)
            
        elif action.action_type == UndoType.CLEAR:
            self.strokes.clear()
            self.shapes.clear()
            self.images.clear()
            
        self.rebuild_spatial_grid()
        self.content_cache_valid = False
        self.update()
    
    def clear_canvas(self):
        """Clear the entire canvas (Undoable)"""
        cleared_data = {
            'strokes': list(self.strokes), 
            'shapes': list(self.shapes), 
            'images': list(self.images)
        }
        
        self.undo_stack.append(UndoAction(UndoType.CLEAR, cleared_data))
        self.redo_stack.clear()
        
        self.strokes.clear()
        self.shapes.clear()
        self.images.clear()
        self.rebuild_spatial_grid()
        self.content_cache_valid = False
        self.update()
    
    
    def set_background_type(self, bg_type):
        """Set background type"""
        self.background_type = bg_type
        self.content_cache_valid = False
        self.bg_cache_valid = False  # Invalidate background cache
        self.update()
    
    def set_background_color(self, color):
        """Set background color"""
        self.background_color = color
        self.content_cache_valid = False
        self.bg_cache_valid = False  # Invalidate background cache
        self.update()
    
    def add_image(self, file_path):
        """Add image from file path"""
        try:
            image = QImage(file_path)
            if image.isNull():
                print(f"Failed to load image: {file_path}")
                return
            # Place image at center of canvas
            img_size = QSize(min(image.width(), 400), min(image.height(), 400))
            img_pos = QPointF((self.width() - img_size.width()) / 2, 
                             (self.height() - img_size.height()) / 2)
            img_obj = ImageObject(image=image, position=img_pos, size=img_size)
            self.images.append(img_obj)
            self.content_cache_valid = False
            self.update()
        except Exception as e:
            print(f"Error adding image: {e}")
    
    def resizeEvent(self, event):
        """Invalidate cache on resize"""
        self.content_cache_valid = False
        super().resizeEvent(event)
    
    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        # 1. Draw background (always at bottom)
        self._draw_background(painter)
        
        # 2. Draw Cached Content (Optimized)
        if not self.content_cache_valid or self.cached_pixmap is None or self.cached_pixmap.size() != self.size():
             # Rebuild cache
             self.cached_pixmap = QPixmap(self.size())
             self.cached_pixmap.fill(Qt.GlobalColor.transparent)
             
             cache_painter = QPainter(self.cached_pixmap)
             cache_painter.setRenderHint(QPainter.RenderHint.Antialiasing)
             cache_painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
             
             # Draw images
             for i, img_obj in enumerate(self.images):
                 if img_obj is None:  # Skip None objects from failed loads
                     continue
                 if i not in self.selected_images:
                     cache_painter.drawImage(QRectF(img_obj.position, QSizeF(img_obj.size)), img_obj.image)
             
             # Draw shapes
             for i, shape in enumerate(self.shapes):
                 if i not in self.selected_shapes:
                     self._draw_shape(cache_painter, shape)
                 
             # Draw strokes
             for i, stroke in enumerate(self.strokes):
                 # Skip selected strokes (they are drawn dynamically)
                 if i not in self.selected_strokes and not stroke.is_deleted:
                     self._draw_stroke(cache_painter, stroke)
                 
             cache_painter.end()
             self.content_cache_valid = True 
             
        # Draw the cached static content
        painter.drawPixmap(0, 0, self.cached_pixmap)
        
        # 3. Dynamic Content (Current drawing)
        # We draw this directly to widget (or temp layer if complex) on top of cache
        if hasattr(self, 'current_stroke') and self.current_stroke and len(self.current_stroke.points) > 1:
             # For eraser preview or live drawing
             # If eraser, we might need to draw into a temp layer to composite correctly?
             # Standard "SourceOver" is fine for pen, but Eraser needs care.
             if self.current_stroke.tool == ToolType.ERASER:
                 painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationOut) # Incorrect for QWidget
                 # Eraser on Widget requires drawing background over? Or just simple overlay?
                 # If we draw 'Clear' on widget, it shows black?
                 # Actually, Eraser previews usually just outline.
                 pass
             else:
                 self._draw_stroke(painter, self.current_stroke)
                 
        if hasattr(self, 'current_shape') and self.current_shape and self.shape_start:
             self._draw_shape(painter, self.current_shape, preview=True)

        # 4. Draw Selected Items Dynamically (So we don't invalidate cache on move)
        # Note: When moving, the stroke data IS updated in real-time in the list,
        # BUT we skipped drawing them in the cache. So we draw them here.
        
        # Images
        for i in self.selected_images:
            if i < len(self.images):
                img_obj = self.images[i]
                if img_obj is None:  # Skip None objects
                    continue
                painter.drawImage(QRectF(img_obj.position, QSizeF(img_obj.size)), img_obj.image)
        
        # Shapes
        for i in self.selected_shapes:
            if i < len(self.shapes):
                self._draw_shape(painter, self.shapes[i])
                
        # Strokes
        for i in self.selected_strokes:
             if i < len(self.strokes):
                 self._draw_stroke(painter, self.strokes[i])

        
        # 3. Overlays (Selection, Ruler, Cursor)
        
        # Draw selection rectangle
        # Draw selection rectangle
        if self.selection_rect:
            painter.setPen(QPen(QColor(0, 120, 215), 1, Qt.PenStyle.DashLine))
            painter.setBrush(QColor(0, 120, 215, 20))
            painter.drawRect(self.selection_rect)
            
            # Draw resize handles if single image selected
            if self.current_tool == ToolType.SELECT and len(self.selected_images) == 1 and not self.selected_strokes and not self.selected_shapes:
                self._draw_resize_handles(painter, self.selection_rect)
        
        # Draw region selection rectangle
        if self.region_rect:
            painter.setPen(QPen(QColor(0, 120, 215), 1, Qt.PenStyle.DashLine))
            painter.setBrush(QColor(0, 120, 215, 20))
            painter.drawRect(self.region_rect.normalized())
        
            
        # Draw Eraser Cursor
        if self.current_tool == ToolType.ERASER:
            cursor_pos = self.mapFromGlobal(QCursor.pos())
            # Convert to QPointF to support float dimensions
            cursor_pos_f = QPointF(cursor_pos)
            painter.setPen(QPen(Qt.GlobalColor.black, 1, Qt.PenStyle.SolidLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(cursor_pos_f, self.eraser_width/2, self.eraser_width/2)
            # Inner white circle for visibility on dark backgrounds
            painter.drawEllipse(cursor_pos_f, self.eraser_width/2 - 1, self.eraser_width/2 - 1)

    def render_to_painter(self, painter: QPainter, target_rect: QRectF = None):
        """Render canvas content to a specific painter (used for Export/PDF)
        
        Uses layered rendering to prevent eraser from cutting through background.
        """
        # Get canvas dimensions for creating layers
        canvas_rect = target_rect if target_rect else QRectF(0, 0, self.width(), self.height())
        w = int(canvas_rect.width())
        h = int(canvas_rect.height())
        
        # LAYERED RENDERING FIX
        # Problem: Direct rendering with CompositionMode_Clear erases background
        # Solution: Render background and content separately, then compose
        
        # Layer 1: Background (with grid/pattern)
        bg_layer = QImage(w, h, QImage.Format.Format_ARGB32)
        bg_layer.fill(self.background_color)
        
        bg_painter = QPainter(bg_layer)
        bg_painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw background pattern (if any)
        self._draw_background(bg_painter)
        bg_painter.end()
        
        # Layer 2: Content (transparent, with eraser support)
        content_layer = QImage(w, h, QImage.Format.Format_ARGB32)
        content_layer.fill(Qt.GlobalColor.transparent)
        
        content_painter = QPainter(content_layer)
        content_painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        content_painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        # Draw images
        for img_obj in self.images:
            if img_obj is None:  # Skip None objects
                continue
            content_painter.drawImage(QRectF(img_obj.position, QSizeF(img_obj.size)), img_obj.image)
            
        # Draw shapes
        for shape in self.shapes:
            self._draw_shape(content_painter, shape)
            
        # Draw strokes
        for stroke in self.strokes:
            self._draw_stroke(content_painter, stroke)
            
        content_painter.end()
        
        # Composite: Draw background first, then content on top
        painter.drawImage(0, 0, bg_layer)
        painter.drawImage(0, 0, content_layer)

    def get_high_quality_image(self, scale=3.0) -> QImage:
        """Render the canvas at high resolution for export"""
        size = self.size() * scale
        image = QImage(size, QImage.Format.Format_ARGB32_Premultiplied)
        
        # Set DPR but use manual scaling for content due to QPainter-QImage quirk
        # image.setDevicePixelRatio(scale) # Optional, metadata only
        
        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        
        # Scale for high-res output
        painter.scale(scale, scale)
        
        self.render_to_painter(painter)
            
        painter.end()
        image.setDevicePixelRatio(scale) # Ensure high-DPI display
        return image
    
    def _draw_background(self, painter: QPainter):
        """Draw background with selected theme"""
        # Use cached background if valid
        if not self.bg_cache_valid or not self.background_cache:
            self.background_cache = QPixmap(self.size())
            bg_painter = QPainter(self.background_cache)
            bg_painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Fill base color
            bg_painter.fillRect(self.background_cache.rect(), self.background_color)
            
            # Draw pattern
            if self.background_type == BackgroundType.DOTS:
                self._draw_dots(bg_painter)
            elif self.background_type == BackgroundType.GRID:
                self._draw_grid(bg_painter)
            elif self.background_type == BackgroundType.LINES:
                self._draw_lines(bg_painter)
            elif self.background_type == BackgroundType.LINES_WITH_MARGIN:
                self._draw_lines_with_margin(bg_painter)
            elif self.background_type == BackgroundType.GRAPH:
                self._draw_graph(bg_painter)
            
            bg_painter.end()
            self.bg_cache_valid = True
        
        painter.drawPixmap(0, 0, self.background_cache)
    
    def _draw_dots(self, painter: QPainter):
        """Draw dotted grid (Optimized with drawPoints)"""
        painter.setPen(QPen(self.grid_color, 2))
        spacing = self.grid_spacing
        
        points = []
        for x in range(0, self.width(), spacing):
            for y in range(0, self.height(), spacing):
                points.append(QPointF(x, y))
        
        if points:
            painter.drawPoints(QPolygonF(points))
    
    def _draw_grid(self, painter: QPainter):
        """Draw grid lines"""
        painter.setPen(QPen(self.grid_color, 1))
        spacing = self.grid_spacing
        
        # Vertical lines
        for x in range(0, self.width(), spacing):
            painter.drawLine(x, 0, x, self.height())
        
        # Horizontal lines
        for y in range(0, self.height(), spacing):
            painter.drawLine(0, y, self.width(), y)
    
    def _draw_lines(self, painter: QPainter):
        """Draw horizontal lines (ruled paper)"""
        painter.setPen(QPen(self.grid_color, 1))
        spacing = self.grid_spacing
        
        for y in range(0, self.height(), spacing):
            painter.drawLine(0, y, self.width(), y)

    def _draw_lines_with_margin(self, painter: QPainter):
        """Draw horizontal lines with a vertical red margin"""
        # 1. Draw horizontal lines (blue-ish)
        # Use a slightly lighter blue for the horizontal lines
        rule_color = QColor(100, 149, 237, 100) # Cornflower blue, semi-transparent
        painter.setPen(QPen(rule_color, 1))
        spacing = self.grid_spacing
        
        for y in range(spacing, self.height(), spacing):
            painter.drawLine(0, y, self.width(), y)
            
        # 2. Draw vertical margin line (red)
        margin_x = 80 # Standard margin width
        margin_color = QColor(255, 100, 100, 150) # Red, semi-transparent
        painter.setPen(QPen(margin_color, 2))
        painter.drawLine(margin_x, 0, margin_x, self.height())
    
    def _draw_graph(self, painter: QPainter):
        """Draw graph paper (grid + dots at intersections)"""
        # Draw grid
        painter.setPen(QPen(self.grid_color, 1, Qt.PenStyle.DotLine))
        spacing = self.grid_spacing
        
        for x in range(0, self.width(), spacing):
            painter.drawLine(x, 0, x, self.height())
        
        for y in range(0, self.height(), spacing):
            painter.drawLine(0, y, self.width(), y)
        
        # Emphasize intersections
        painter.setPen(QPen(self.grid_color.lighter(150), 3))
        for x in range(0, self.width(), spacing):
            for y in range(0, self.height(), spacing):
                painter.drawPoint(x, y)
    
    def _draw_stroke(self, painter: QPainter, stroke: Stroke):
        """Draw a stroke with advanced rendering using cached path"""
        # [FIX] Immediate visual feedback for soft delete
        if getattr(stroke, 'is_deleted', False):
            return

        if len(stroke.points) < 2:
            return
        
        # Use cached path from Stroke object
        path = stroke.path
        
        # Get pen style
        pen_style = self.pen_styles.get(stroke.tool, self.pen_styles[ToolType.PEN])
        
        # Configure pen
        color = QColor(stroke.color)
        
        if stroke.tool == ToolType.ERASER:
            # IMPORTANT: For eraser, use Clear mode to remove content but keep background
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            pen = QPen(Qt.GlobalColor.transparent, stroke.width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            painter.drawPath(path)
            # Reset composition mode
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            return
            
        elif stroke.tool == ToolType.PENCIL:
            # Pencil gets special texture effect
            color.setAlpha(int(155 * stroke.opacity))
            width = stroke.width
        else:
            color.setAlpha(int(255 * stroke.opacity * pen_style['opacity']))
            width = stroke.width
        
        pen = QPen(color, width, Qt.PenStyle.SolidLine, pen_style['cap'], Qt.PenJoinStyle.RoundJoin)
        
        # Draw the path
        painter.setPen(pen)
        painter.drawPath(path)
    
    
    def _draw_shape(self, painter: QPainter, shape: ShapeObject, preview: bool = False):
        """Draw geometric shape"""
        color = QColor(shape.color)
        if preview:
            color.setAlpha(128)
        
        # Set brush to NoBrush (no fill for shapes)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        # Set pen for outline
        pen = QPen(color, shape.width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        
        if shape.shape_type == ToolType.LINE:
            painter.drawLine(QLineF(shape.start, shape.end))
        elif shape.shape_type == ToolType.RECTANGLE:
            rect = QRectF(shape.start, shape.end).normalized()
            painter.drawRect(rect)
        elif shape.shape_type == ToolType.CIRCLE:
            rect = QRectF(shape.start, shape.end).normalized()
            painter.drawEllipse(rect)
        elif shape.shape_type == ToolType.ARROW:
            # Draw line
            painter.drawLine(shape.start, shape.end)
            
            # Draw arrow head
            line = QLineF(shape.start, shape.end)
            angle = math.atan2(-line.dy(), line.dx())
            arrow_size = shape.width * 3
            
            arrow_p1 = shape.end - QPointF(math.sin(angle + math.pi/3) * arrow_size,
                                         math.cos(angle + math.pi/3) * arrow_size)
            arrow_p2 = shape.end - QPointF(math.sin(angle + math.pi - math.pi/3) * arrow_size,
                                         math.cos(angle + math.pi - math.pi/3) * arrow_size)
            
            arrow_head = QPolygonF([shape.end, arrow_p1, arrow_p2])
            painter.setBrush(QBrush(shape.color))
            painter.drawPolygon(arrow_head)
            
        elif shape.shape_type == ToolType.DOUBLE_ARROW:
            # Draw line
            painter.drawLine(shape.start, shape.end)
            
            # Draw arrow heads at both ends
            line = QLineF(shape.start, shape.end)
            angle = math.atan2(-line.dy(), line.dx())
            arrow_size = shape.width * 3
            
            # End arrow
            p1 = shape.end - QPointF(math.sin(angle + math.pi/3) * arrow_size,
                                   math.cos(angle + math.pi/3) * arrow_size)
            p2 = shape.end - QPointF(math.sin(angle + math.pi - math.pi/3) * arrow_size,
                                   math.cos(angle + math.pi - math.pi/3) * arrow_size)
            painter.setBrush(QBrush(shape.color))
            painter.drawPolygon(QPolygonF([shape.end, p1, p2]))
            
            # Start arrow (reverse angle)
            p3 = shape.start + QPointF(math.sin(angle + math.pi/3) * arrow_size,
                                     math.cos(angle + math.pi/3) * arrow_size)
            p4 = shape.start + QPointF(math.sin(angle + math.pi - math.pi/3) * arrow_size,
                                     math.cos(angle + math.pi - math.pi/3) * arrow_size)
            painter.drawPolygon(QPolygonF([shape.start, p3, p4]))
    
    
    def tabletEvent(self, event: QTabletEvent):
        """Handle stylus/tablet input"""
        pos = event.position()
        pressure = event.pressure()
        
        if event.pointerType() == QPointingDevice.PointerType.Eraser:
            # Auto-switch to eraser with stylus back
            old_tool = self.current_tool
            self.current_tool = ToolType.ERASER
            
            if event.type() == QEvent.Type.TabletPress:
                self._start_stroke(pos, pressure)
            elif event.type() == QEvent.Type.TabletMove:
                if self.current_stroke:
                    self._continue_stroke(pos, pressure)
            elif event.type() == QEvent.Type.TabletRelease:
                self._end_stroke()
                self.current_tool = old_tool
        else:
            # Handle tools based on type
            if self.current_tool in [ToolType.LINE, ToolType.RECTANGLE, ToolType.CIRCLE, ToolType.ARROW, ToolType.DOUBLE_ARROW]:
                # Shape tools
                if event.type() == QEvent.Type.TabletPress:
                    self._start_shape(pos)
                elif event.type() == QEvent.Type.TabletMove:
                    self._update_shape(pos)
                elif event.type() == QEvent.Type.TabletRelease:
                    self._end_shape()
            elif self.current_tool == ToolType.STROKE_ERASER:
                # Stroke eraser
                if event.type() == QEvent.Type.TabletPress or event.type() == QEvent.Type.TabletMove:
                    self._erase_stroke_at(pos)
            elif self.current_tool == ToolType.SELECT:
                 # Forward to mouse event handler for selection logic as it's complex
                 # we can ignore tablet specific properties for selection for now
                 pass 
            else:
                # Pen/Eraser tools
                if event.type() == QEvent.Type.TabletPress:
                    self._start_stroke(pos, pressure)
                elif event.type() == QEvent.Type.TabletMove:
                    if self.current_stroke:
                        self._continue_stroke(pos, pressure)
                elif event.type() == QEvent.Type.TabletRelease:
                    self._end_stroke()
        
        event.accept()
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press"""
        if event.button() == Qt.MouseButton.MiddleButton or (event.button() == Qt.MouseButton.LeftButton and event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            self.is_panning = True
            self.last_pan_point = event.position()
        elif event.button() == Qt.MouseButton.LeftButton:
            if self.current_tool == ToolType.SELECT:
                # 1. Check Resize Handles first (if single item selected)
                has_single_image = len(self.selected_images) == 1 and not self.selected_strokes and not self.selected_shapes
                has_single_shape = len(self.selected_shapes) == 1 and not self.selected_strokes and not self.selected_images
                
                if (has_single_image or has_single_shape) and self.selection_rect:
                    handles = self._get_resize_handles(self.selection_rect)
                    for idx, handle in enumerate(handles):
                        if handle.contains(event.position()):
                            self.is_resizing = True
                            self.resize_handle_idx = idx
                            self.resize_original_rect = QRectF(self.selection_rect)
                            self.resize_start_pos = event.position()
                            return
                
                # 2. Check Selection Move
                if self.selection_rect and self.selection_rect.contains(event.position()):
                    self.is_moving_selection = True
                    self.selection_offset = event.position() - self.selection_rect.topLeft()
                    return  # CRITICAL: Prevent falling through to selection clearing below
                else:
                    # 3. New Selection (Check for Click-to-Select)
                    clicked_item = False
                    
                    # Check Images (Top-most first)
                    for idx in reversed(range(len(self.images))):
                        img = self.images[idx]
                        img_rect = QRectF(img.position, QSizeF(img.size))
                        if img_rect.contains(event.position()):
                            self.selected_images = [idx]
                            self.selected_strokes.clear()
                            self.selected_shapes.clear()
                            self.selection_rect = img_rect
                            self.selection_start = img_rect.topLeft() # Just logical start
                            clicked_item = True
                            self.update()
                            return

                    # Clicking outside - clear selection immediately if something was selected
                    if self.current_tool == ToolType.SELECT:
                        # Check if we had a selection to clear
                        if self.selected_strokes or self.selected_shapes or self.selected_images:
                            # Deselect everything immediately
                            self.content_cache_valid = False
                            self.selected_strokes.clear()
                            self.selected_shapes.clear()
                            self.selected_images.clear()
                            self.selection_rect = None
                            self.selection_start = None
                            self.update()  # Immediate visual update
                        else:
                            # No previous selection - start new rubber band selection
                            self.selection_start = event.position()
                            self.selection_rect = QRectF(event.position(), event.position())

            # elif self.current_tool == ToolType.REGION_SELECT:  <-- Moved inside main logic
            #    pass
            elif self.current_tool in [ToolType.LINE, ToolType.RECTANGLE, ToolType.CIRCLE, ToolType.ARROW, ToolType.DOUBLE_ARROW]:
                self._start_shape(event.position())
            elif self.current_tool == ToolType.STROKE_ERASER:
                self._erase_stroke_at(event.position())
            else:
                self._start_stroke(event.position(), 1.0)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move"""
        if self.is_panning:
            delta = event.position() - self.last_pan_point
            self.pan_offset += delta
            self.last_pan_point = event.position()
            self.content_cache_valid = False
            self.update()
        elif event.buttons() & Qt.MouseButton.LeftButton:
            if self.current_tool == ToolType.SELECT:
                if self.is_resizing and self.resize_original_rect:
                    # Handle Resizing
                    delta = event.position() - self.resize_start_pos
                    new_rect = QRectF(self.resize_original_rect)
                    
                    idx = self.resize_handle_idx
                    # TL, TM, TR, RM, BR, BM, BL, LM
                    if idx in [0, 6, 7]: # Left
                        new_rect.setLeft(min(new_rect.right() - 10, new_rect.left() + delta.x()))
                    if idx in [2, 3, 4]: # Right
                        new_rect.setRight(max(new_rect.left() + 10, new_rect.right() + delta.x()))
                    if idx in [0, 1, 2]: # Top
                        new_rect.setTop(min(new_rect.bottom() - 10, new_rect.top() + delta.y()))
                    if idx in [4, 5, 6]: # Bottom
                        new_rect.setBottom(max(new_rect.top() + 10, new_rect.bottom() + delta.y()))
                    
                    # Update image and selection
                    self.selection_rect = new_rect.normalized()
                    
                    if self.selected_images:
                        img_idx = self.selected_images[0]
                        if img_idx < len(self.images):
                            self.images[img_idx].position = self.selection_rect.topLeft()
                            # Convert QSizeF to QSize for ImageObject
                            self.images[img_idx].size = QSize(int(self.selection_rect.width()), int(self.selection_rect.height()))
                            
                    if self.selected_shapes:
                        shape_idx = self.selected_shapes[0]
                        if shape_idx < len(self.shapes):
                            # Resizing a shape means updating its start/end points to match the new rect
                            # We assume the shape fills the rect for simplicity (standard behavior for rect/circle tools)
                            # For lines, it might distort, but that's expected in box resizing.
                            self.shapes[shape_idx].start = self.selection_rect.topLeft()
                            self.shapes[shape_idx].end = self.selection_rect.bottomRight()
                    
                    
                    self.content_cache_valid = False
                    self.update()
                    
                elif self.is_moving_selection and self.selection_rect:
                    # Move selection
                    new_pos = event.position() - self.selection_offset
                    delta = new_pos - self.selection_rect.topLeft()
                    
                    # Move selected items
                    for idx in self.selected_strokes:
                        if idx < len(self.strokes):
                            stroke = self.strokes[idx]
                            stroke.points = [(p[0] + delta.x(), p[1] + delta.y(), p[2]) for p in stroke.points]
                            stroke.invalidate_path()
                    
                    for idx in self.selected_shapes:
                        if idx < len(self.shapes):
                            shape = self.shapes[idx]
                            shape.start += delta
                            shape.end += delta
                    
                    for idx in self.selected_images:
                        if idx < len(self.images):
                            self.images[idx].position += delta
                    
                    
                    self.selection_rect.translate(delta)
                    self.content_cache_valid = False
                    self.update()
                elif self.selection_start and self.current_tool == ToolType.SELECT:
                    # Update selection rectangle
                    self.selection_rect = QRectF(self.selection_start, event.position()).normalized()
                    # Only update selection items if in SELECT mode (REGION_SELECT calculates at end)
                    if self.current_tool == ToolType.SELECT:
                        self._update_selection()
                    self.update()
                # Removing separate region_rect logic as we use selection_rect now
                # elif self.current_tool == ToolType.REGION_SELECT:
                #    if self.region_rect:
                #        self.region_rect.setBottomRight(event.position())
                #        self.update()
            # elif self.current_tool == ToolType.REGION_SELECT: <-- Moved inside
            #    pass
            elif self.current_tool in [ToolType.LINE, ToolType.RECTANGLE, ToolType.CIRCLE, ToolType.ARROW, ToolType.DOUBLE_ARROW]:
                self._update_shape(event.position())
            elif self.current_stroke:
                self._continue_stroke(event.position(), 1.0)
            elif self.current_tool == ToolType.STROKE_ERASER:
                 # Adaptive Throttling: Scale from 16ms (60fps) to 33ms (30fps) based on complexity
                 # 0-500 strokes: ~16ms, 1000+ strokes: ~33ms
                 throttle_ms = max(16, min(33, len(self.strokes) * 0.02))
                 
                 current_time = time.time() * 1000
                 if current_time - self.last_eraser_time > throttle_ms:
                     self._erase_stroke_at(event.position())
                     self.last_eraser_time = current_time
        
        # Cursor updates
        if not (event.buttons() & Qt.MouseButton.LeftButton) and self.current_tool == ToolType.SELECT:
             if len(self.selected_images) == 1 and not self.selected_strokes and not self.selected_shapes and self.selection_rect:
                 handles = self._get_resize_handles(self.selection_rect)
                 cursor_set = False
                 cursors = [
                     Qt.CursorShape.SizeFDiagCursor, Qt.CursorShape.SizeVerCursor, Qt.CursorShape.SizeBDiagCursor, 
                     Qt.CursorShape.SizeHorCursor, Qt.CursorShape.SizeFDiagCursor, Qt.CursorShape.SizeVerCursor, 
                     Qt.CursorShape.SizeBDiagCursor, Qt.CursorShape.SizeHorCursor
                 ]
                 for idx, handle in enumerate(handles):
                     if handle.contains(event.position()):
                         self.setCursor(cursors[idx])
                         cursor_set = True
                         break
                 if not cursor_set:
                     if self.selection_rect.contains(event.position()):
                         self.setCursor(Qt.CursorShape.SizeAllCursor)
                     else:
                         self.setCursor(Qt.CursorShape.ArrowCursor)
             elif self.selection_rect and self.selection_rect.contains(event.position()):
                 self.setCursor(Qt.CursorShape.SizeAllCursor)
             else:
                 self.setCursor(Qt.CursorShape.ArrowCursor)
        elif self.current_tool != ToolType.SELECT:
             # Reset to default if not selecting (or handle custom tool cursors)
             self.setCursor(Qt.CursorShape.ArrowCursor)
        
        # Always update for cursor animation when eraser is active
        if self.current_tool == ToolType.ERASER:
            self.update()
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release"""
        # Cleanup deleted strokes (Deferred Deletion)
        # Cleanup deleted strokes (Deferred Deletion with UNDO Support)
        if self.current_tool == ToolType.STROKE_ERASER:
             # Find deleted strokes and their INDICES before removing them
             erased_data = [] # List[(original_index, stroke)]
             
             # Iterate backwards to preserve indices relative to unmodified list? 
             # No, we need original indices. enumerate works.
             # But if we delete multiple, we need to know how to put them back.
             # Simplest: Store (index, stroke). When undoing, insert them back in distinct steps or bulk?
             # If we insert sorted by index, it's fine.
             
             for i, stroke in enumerate(self.strokes):
                 if stroke.is_deleted:
                     stroke.is_deleted = False # Reset flag for storage
                     erased_data.append((i, stroke))
             
             if erased_data:
                 # Remove from strokes list
                 # We must build a new list to remove them
                 self.strokes = [s for s in self.strokes if s not in [x[1] for x in erased_data]]
                 
                 # Push Undo Action
                 self.undo_stack.append(UndoAction(UndoType.ERASE_STROKES, erased_data))
                 self.redo_stack.clear()
                 
                 self.rebuild_spatial_grid()
                 self.content_cache_valid = False
                 self.update()
        
        if event.button() == Qt.MouseButton.MiddleButton or event.button() == Qt.MouseButton.LeftButton:
            if self.is_panning:
                self.is_panning = False
                self.setCursor(Qt.CursorShape.ArrowCursor)
            elif self.current_tool == ToolType.SELECT:
                if self.is_resizing:
                    # Resizing finished - invalidate cache to persist changes
                    self.is_resizing = False
                    self.resize_original_rect = None
                    self.content_cache_valid = False  # Force cache rebuild with new size
                    self.update()  # Final update after resize
                elif self.is_moving_selection:
                    # Moving finished - invalidate cache to persist changes
                    self.is_moving_selection = False
                    self.content_cache_valid = False  # Force cache rebuild with new position
                    self.update()  # Final update after move
                elif self.selection_rect:
                    # New selection drag just finished
                    self._finalize_selection()
                
            # Remove duplicate REGION_SELECT logic - _finalize_selection already handles it
            # elif self.current_tool == ToolType.REGION_SELECT: <-- Removed old logic
            #    pass
            elif self.current_tool in [ToolType.LINE, ToolType.RECTANGLE, ToolType.CIRCLE, ToolType.ARROW, ToolType.DOUBLE_ARROW]:
                self._end_shape()
            else:
                self._end_stroke()
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        # Ctrl+X: Cut region
        if event.key() == Qt.Key.Key_X and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if self.current_tool == ToolType.REGION_SELECT and self.region_rect:
                self._copy_region()
                self._delete_region_content()
                self.region_rect = None
                self.update()
        # Ctrl+C: Copy region
        elif event.key() == Qt.Key.Key_C and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if self.current_tool == ToolType.REGION_SELECT and self.region_rect:
                self._copy_region()
        # Delete: Delete selection or region
        elif event.key() == Qt.Key.Key_Delete or event.key() == Qt.Key.Key_Backspace:
            if self.current_tool == ToolType.SELECT:
                self._delete_selection()
            elif self.current_tool == ToolType.REGION_SELECT and self.region_rect:
                self._delete_region_content()
                self.region_rect = None
                self.update()
        # Escape: Clear selection
        elif event.key() == Qt.Key.Key_Escape:
            if self.current_tool == ToolType.REGION_SELECT:
                self.region_rect = None
                self.update()
            else:
                self._clear_selection()
        super().keyPressEvent(event)
    
    def _update_selection(self):
        """Update which items are selected"""
        if not self.selection_rect:
            return
        
        self.selected_strokes.clear()
        self.selected_shapes.clear()
        self.selected_images.clear()
        
        # Check strokes
        for idx, stroke in enumerate(self.strokes):
            for x, y, _ in stroke.points:
                if self.selection_rect.contains(QPointF(x, y)):
                    if idx not in self.selected_strokes:
                        self.selected_strokes.append(idx)
                    break
        
        # Check shapes
        for idx, shape in enumerate(self.shapes):
            shape_rect = QRectF(shape.start, shape.end).normalized()
            if self.selection_rect.intersects(shape_rect):
                self.selected_shapes.append(idx)
        
        # Check images
        for idx, img_obj in enumerate(self.images):
            img_rect = QRectF(img_obj.position, QSizeF(img_obj.size))
            if self.selection_rect.intersects(img_rect):
                self.selected_images.append(idx)

        self.content_cache_valid = False
        self.update()
    
    def _split_items_in_region(self, rect: QRectF):
        """Split strokes and images at the boundary of the rect"""
        new_strokes = []
        strokes_to_remove = []
        
        # 1. Split Strokes
        for i, stroke in enumerate(self.strokes):
            if not stroke.path.boundingRect().intersects(rect):
                continue
            
            # Check if stroke needs splitting (crosses boundary)
            points = stroke.points
            if not points: continue
            
            segments = []
            current_segment = []
            
            # Determine start state
            p0 = points[0]
            is_inside = rect.contains(QPointF(p0[0], p0[1]))
            current_segment.append(p0)
            
            state_changed = False
            
            for j in range(1, len(points)):
                p1 = points[j]
                p1_pt = QPointF(p1[0], p1[1])
                now_inside = rect.contains(p1_pt)
                
                if now_inside != is_inside:
                    # Crossing boundary!
                    state_changed = True
                    # Find intersection (simplified: mid-point or linear interp)
                    # For handwriting, simple linear interp is fine
                    p_prev = points[j-1]
                    
                    # Intersect Line(p_prev, p1) with Rect
                    # Simplified: just finish current segment at prev, start new at current
                    # Or insert a "cut" point.
                    # Let's just break here.
                    
                    segments.append((is_inside, current_segment))
                    current_segment = [p1] # Start new segment
                    is_inside = now_inside
                else:
                    current_segment.append(p1)
            
            segments.append((is_inside, current_segment))
            
            if state_changed:
                strokes_to_remove.append(i)
                for inside, pts in segments:
                    if len(pts) > 1:
                        new_s = Stroke(pts, stroke.color, stroke.width, stroke.tool)
                        # Re-calculate path/boundingRect for new stroke
                        # This usually happens in __init__ or we call update
                        # Looking at Stroke class (assumed), it probably needs init
                        new_strokes.append(new_s)
        
        # Remove old strokes and add new ones
        for i in sorted(strokes_to_remove, reverse=True):
            self.strokes.pop(i)
        self.strokes.extend(new_strokes)
        
        # 2. Split Images (Crop) - Use safe copy to prevent index errors
        images_copy = self.images.copy()  # SAFE: Prevent modification during iteration
        new_images = []
        
        for img_obj in images_copy:  # No index dependency
            # Explicitly cast to QSizeF to prevent TypeError (QRectF + QSize mismatch)
            # Ensuring width/height are floats
            size_f = QSizeF(float(img_obj.size.width()), float(img_obj.size.height()))
            img_rect = QRectF(img_obj.position, size_f)
            
            if rect.contains(img_rect):
                continue # Fully inside, no need to split
            
            if rect.intersects(img_rect):
                # Intersection rect relative to global
                inter = rect.intersected(img_rect)
                if inter.isEmpty(): continue
                
                # Copy "Inside" part
                # Map global inter rect to image local coords
                local_x = inter.x() - img_obj.position.x()
                local_y = inter.y() - img_obj.position.y()
                
                # Crop logic
                # Scale if needed? Assuming ImageObject.image size matches QSizeF size logic
                # But QImage uses integer pixels.
                
                # Ensure coords are valid image pixels
                src_rect = QRect(int(local_x), int(local_y), int(inter.width()), int(inter.height()))
                
                if src_rect.isValid():
                    cropped_img = img_obj.image.copy(src_rect)
                    # FIX: Pass size argument (QSize) to ImageObject constructor
                    new_size = QSize(src_rect.width(), src_rect.height())
                    new_img_obj = ImageObject(cropped_img, inter.topLeft(), new_size)
                    new_images.append(new_img_obj)
                    
                    # Cut "hole" in original image (Outcome: Original becomes "Outside" part)
                    # We utilize QPainter to clear the rect
                    painter = QPainter(img_obj.image)
                    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
                    painter.eraseRect(src_rect)
                    painter.end()
                    
                    # We keep the original image (modified) AND add the new "Inside" chunk
                    # So effectively we split it.
                    
        self.images.extend(new_images)

        self.content_cache_valid = False
        # DO NOT call update() here - let _finalize_selection handle it to prevent flicker
    
    def _finalize_selection(self):
        """Finalize selection"""
        self._update_selection()
        
        # CRITICAL: Reset selection_start to prevent ghost rectangles
        self.selection_start = None
        
        # Clear or recalculate selection rect
        if not self.selected_strokes and not self.selected_shapes and not self.selected_images:
            # Nothing selected - clear everything
            self.selection_rect = None

        self.update()  # Single update call at the end
    
    def _calculate_selection_bounds(self):
        """Calculate bounding rectangle for all selected items"""
        if not self.selected_strokes and not self.selected_shapes and not self.selected_images:
            return None
        
        min_x = float('inf')
        min_y = float('inf')
        max_x = float('-inf')
        max_y = float('-inf')
        
        # Check selected strokes
        for idx in self.selected_strokes:
            if idx < len(self.strokes):
                stroke = self.strokes[idx]
                for x, y, _ in stroke.points:
                    min_x = min(min_x, x)
                    min_y = min(min_y, y)
                    max_x = max(max_x, x)
                    max_y = max(max_y, y)
        
        # Check selected shapes
        for idx in self.selected_shapes:
            if idx < len(self.shapes):
                shape = self.shapes[idx]
                min_x = min(min_x, shape.start.x(), shape.end.x())
                min_y = min(min_y, shape.start.y(), shape.end.y())
                max_x = max(max_x, shape.start.x(), shape.end.x())
                max_y = max(max_y, shape.start.y(), shape.end.y())
        
        # Check selected images
        for idx in self.selected_images:
            if idx < len(self.images):
                img = self.images[idx]
                min_x = min(min_x, img.position.x())
                min_y = min(min_y, img.position.y())
                max_x = max(max_x, img.position.x() + img.size.width())
                max_y = max(max_y, img.position.y() + img.size.height())
        
        if min_x == float('inf'):
            return None
        
        return QRectF(QPointF(min_x, min_y), QPointF(max_x, max_y))
    
    def _get_resize_handles(self, rect):
        """Get resize handles for a rectangle"""
        handles = []
        size = 8
        half = size / 2
        
        # TL, TM, TR, RM, BR, BM, BL, LM
        handles.append(QRectF(rect.left() - half, rect.top() - half, size, size))
        handles.append(QRectF(rect.center().x() - half, rect.top() - half, size, size))
        handles.append(QRectF(rect.right() - half, rect.top() - half, size, size))
        handles.append(QRectF(rect.right() - half, rect.center().y() - half, size, size))
        handles.append(QRectF(rect.right() - half, rect.bottom() - half, size, size))
        handles.append(QRectF(rect.center().x() - half, rect.bottom() - half, size, size))
        handles.append(QRectF(rect.left() - half, rect.bottom() - half, size, size))
        handles.append(QRectF(rect.left() - half, rect.center().y() - half, size, size))
        
        return handles

    def _draw_resize_handles(self, painter, rect):
        """Draw resize handles"""
        handles = self._get_resize_handles(rect)
        painter.setPen(QPen(QColor(0, 120, 215), 1))
        painter.setBrush(QBrush(Qt.GlobalColor.white))
        for handle in handles:
            painter.drawRect(handle)
    
    def _get_handle_at_position(self, pos):
        """Get resize handle index at position, or -1 if none"""
        if not self.selection_rect:
            return -1
        
        handles = self._get_resize_handles(self.selection_rect)
        for i, handle in enumerate(handles):
            if handle.contains(pos):
                return i
        return -1
            
    def _clear_selection(self):
        """Clear current selection"""
        self.selection_rect = None
        self.selected_strokes.clear()
        self.selected_shapes.clear()
        self.selected_images.clear()
        self.update()
    
    def _delete_selection(self):
        """Delete selected items"""
        # Delete in reverse order to maintain indices
        for idx in sorted(self.selected_strokes, reverse=True):
            if idx < len(self.strokes):
                self.strokes.pop(idx)
        
        for idx in sorted(self.selected_shapes, reverse=True):
            if idx < len(self.shapes):
                self.shapes.pop(idx)
        
        for idx in sorted(self.selected_images, reverse=True):
            if idx < len(self.images):
                self.images.pop(idx)
        
        self._clear_selection()
        self.content_cache_valid = False
        self.update()
    
    def _capture_region(self):
        """Capture region - visual feedback only"""
        if self.region_rect:
            self._copy_region()
            print("Region copied to clipboard")
            # Optional: Visual feedback or auto-clear?
            # self.region_rect = None 
            # self.update()
    
    def _copy_region(self):
        """Copy region to clipboard"""
        if not self.region_rect:
            return
        rect = self.region_rect.normalized().toRect()
        if rect.width() <= 0 or rect.height() <= 0: return

        region_image = QImage(int(rect.width()), int(rect.height()), QImage.Format.Format_ARGB32)
        region_image.fill(Qt.GlobalColor.transparent)
        painter = QPainter(region_image)
        painter.translate(-rect.topLeft())
        self._draw_background(painter)
        for img_obj in self.images:
            if img_obj is None:  # Skip None objects
                continue
            if rect.intersects(QRectF(img_obj.position, img_obj.size)):
                painter.drawImage(QRectF(img_obj.position, QSizeF(img_obj.size)), img_obj.image)
        for shape in self.shapes:
            if rect.intersects(QRectF(shape.start, shape.end).normalized()):
                self._draw_shape(painter, shape)
        for stroke in self.strokes:
            if rect.intersects(stroke.path.boundingRect()):
                self._draw_stroke(painter, stroke)
        painter.end()
        QApplication.clipboard().setImage(region_image)
    
    def _delete_region_content(self):
        """Delete content within region"""
        if not self.region_rect:
            return
        rect = self.region_rect.normalized()
        self.images = [img for img in self.images if not rect.intersects(QRectF(img.position, img.size))]
        self.shapes = [s for s in self.shapes if not rect.intersects(QRectF(s.start, s.end).normalized())]
        self.strokes = [s for s in self.strokes if not rect.intersects(s.path.boundingRect())]
        self.strokes = [s for s in self.strokes if not rect.intersects(s.path.boundingRect())]
        self.content_cache_valid = False
        self.update()
    
    def wheelEvent(self, event):
        """Handle zoom with mouse wheel"""
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            zoom_factor = 1.1 if delta > 0 else 0.9
            self.zoom_level *= zoom_factor
            self.zoom_level = max(0.1, min(5.0, self.zoom_level))
            self.content_cache_valid = False
            self.update()
    
    def _start_stroke(self, pos: QPointF, pressure: float):
        """Start a new stroke"""
        if self.current_tool in self.pen_styles:
            style = self.pen_styles[self.current_tool]
            width = self.pen_width * pressure
            opacity = style['opacity']
        else:
            width = self.eraser_width if self.current_tool == ToolType.ERASER else self.pen_width
            opacity = 1.0
        
        self.current_stroke = Stroke(
            points=[(pos.x(), pos.y(), pressure)],
            color=self.current_color,
            width=width,
            tool=self.current_tool,
            opacity=opacity,
            smoothness=self.smoothing_level
        )
        self.update()
    
    def _continue_stroke(self, pos: QPointF, pressure: float):
        """Add point to current stroke"""
        if self.current_stroke:
            self.current_stroke.points.append((pos.x(), pos.y(), pressure))
            self.current_stroke.invalidate_path()
            self.update()
    
    def _end_stroke(self):
        """Finish current stroke"""
        if self.current_stroke and len(self.current_stroke.points) > 1:
            self.strokes.append(self.current_stroke)
            
            # Undo Logic
            self.undo_stack.append(UndoAction(UndoType.ADD_STROKE, self.current_stroke))
            # Memory Protection: Limit undo stack size
            if len(self.undo_stack) > 50:
                self.undo_stack.pop(0)
            self.redo_stack.clear()
            
            self.stroke_added.emit()
            self.content_cache_valid = False

        
        self.current_stroke = None
        self.update()
    
    def _start_shape(self, pos: QPointF):
        """Start drawing a shape"""
        self.shape_start = pos
        self.current_shape = ShapeObject(
            shape_type=self.current_tool,
            start=pos,
            end=pos,
            color=self.current_color,
            width=self.pen_width
        )
        self.update()
    
    def _update_shape(self, pos: QPointF):
        """Update shape being drawn"""
        if self.current_shape:
            self.current_shape.end = pos
            self.update()
            self.update()
            
    def get_grid_key(self, x: float, y: float) -> Tuple[int, int]:
        """Fast spatial grid lookup"""
        return (int(x // self.grid_size), int(y // self.grid_size))
        
    def rebuild_spatial_grid(self):
        """Rebuild spatial index"""
        self.spatial_grid.clear()
        for i, stroke in enumerate(self.strokes):
            # Safe bounding rect check
            if not stroke.points:
                continue
                
            rect = stroke.path.boundingRect()
            if rect.isEmpty():
                continue
                
            # Index stroke in cells covering its bounding box
            start_x, start_y = self.get_grid_key(rect.left(), rect.top())
            end_x, end_y = self.get_grid_key(rect.right(), rect.bottom())
            
            for gx in range(start_x, end_x + 1):
                for gy in range(start_y, end_y + 1):
                    key = (gx, gy)
                    if key not in self.spatial_grid:
                        self.spatial_grid[key] = []
                    self.spatial_grid[key].append(i)
    
    def _end_shape(self):
        """Finish shape"""
        if self.current_shape:
            self.shapes.append(self.current_shape)
            
            # Record Undo Action
            self.undo_stack.append(UndoAction(UndoType.ADD_SHAPE, self.current_shape))
            self.redo_stack.clear()
            
            self.current_shape = None
            self.shape_start = None
            self.content_cache_valid = False
            self.update()
    
    def _erase_stroke_at(self, pos: QPointF):
        """Erase stroke at position (Optimization: Spatial Hash Grid)"""
        # 1. Determine grid cell for eraser position
        grid_x, grid_y = self.get_grid_key(pos.x(), pos.y())
        
        # 2. Check nearby cells (3x3 area) in case stroke is on boundary
        nearby_keys = [
            (grid_x + dx, grid_y + dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1]
        ]
        
        eraser_rect = QRectF(pos.x() - 10, pos.y() - 10, 20, 20)
        potential_indices = set()
        
        # 3. Collect unique stroke indices from relevant grid cells
        for key in nearby_keys:
            if key in self.spatial_grid:
                potential_indices.update(self.spatial_grid[key])
        
        # 4. Check candidates
        # Iterate in reverse to safely delete (though we return on first delete anyway)
        sorted_indices = sorted(list(potential_indices), reverse=True)
        
        for i in sorted_indices:
            if i >= len(self.strokes): 
                # Safety check against stale grid
                continue
                
            stroke = self.strokes[i]
            
            # Skip already deleted
            if stroke.is_deleted:
                continue
                
            # Fast rejection
            if not eraser_rect.intersects(stroke.path.boundingRect()):
                continue
                
            # Precise intersection
            if stroke.path.intersects(eraser_rect):
                # SOFT DELETE: Mark as deleted, don't remove from list yet
                stroke.is_deleted = True
                
                # Do NOT rebuild grid (expensive)
                # self.rebuild_spatial_grid()
                
                self.content_cache_valid = False
                self.update()
                # Return immediately to avoid stale index issues
                return

        # 5. Check Shapes (Linear scan as shapes are usually few)
        for i, shape in enumerate(self.shapes):
            path = QPainterPath()
            if shape.shape_type == ToolType.LINE:
                path.moveTo(shape.start)
                path.lineTo(shape.end)
            elif shape.shape_type == ToolType.RECTANGLE:
                path.addRect(QRectF(shape.start, shape.end).normalized())
            elif shape.shape_type == ToolType.CIRCLE:
                path.addEllipse(QRectF(shape.start, shape.end).normalized())
            elif shape.shape_type == ToolType.ARROW or shape.shape_type == ToolType.DOUBLE_ARROW:
                path.moveTo(shape.start)
                path.lineTo(shape.end)
            
            # Create a stroker to give the shape path some width for intersection
            stroker = QPainterPathStroker()
            stroker.setWidth(max(10, shape.width + 5)) # Give it a hit-box
            shape_path = stroker.createStroke(path)
            
            if shape_path.intersects(eraser_rect):
                 # Hard delete for shapes (simplest for now)
                 self.shapes.pop(i)
                 
                 # Record Undo (Optimistic, ideally should be unified with stroke eraser undo batch)
                 # But since stroke eraser uses "Deferred Deletion" on mouse release, mixing immediate shape delete might split undo history.
                 # For now, let's treat it as immediate action or we need to add is_deleted to ShapeObject.
                 # Let's add is_deleted to ShapeObject to keep it consistent!
                 # Wait, ShapeObject is a dataclass without that field yet.
                 # For now, just direct delete.
                 
                 self.content_cache_valid = False
                 self.update()
                 return
    
    def add_image(self, file_path):
        """Add an image to the canvas"""
        try:
            from PyQt6.QtCore import QFile
            image = QImage(file_path)
            if image.isNull():
                print(f"Failed to load image: {file_path}")
                return
            
            # Create ImageObject at center of viewport
            # Position at center with reasonable size
            img_width = min(image.width(), 400)
            img_height = min(image.height(), 400)
            pos_x = (self.width() - img_width) / 2
            pos_y = (self.height() - img_height) / 2
            
            img_obj = ImageObject(
                image=image,
                position=QPointF(pos_x, pos_y),
                size=QSize(img_width, img_height)
            )
            self.images.append(img_obj)
            
            # Record Undo Action
            self.undo_stack.append(UndoAction(UndoType.ADD_IMAGE, img_obj))
            self.redo_stack.clear()
            
            # CRITICAL: Invalidate cache and trigger repaint
            self.content_cache_valid = False
            self.update()
            
        except Exception as e:
            print(f"Error adding image: {e}")
            import traceback
            traceback.print_exc()


class ScrbleInkPro(QMainWindow):
    """Professional Scrble Ink Application"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Professional Scrble Ink")
        self.setGeometry(50, 50, 1400, 900)
        
        # Color palette - MUST be defined before creating toolbars
        self.color_palette = [
            QColor(0, 0, 0), QColor(255, 255, 255), QColor(255, 0, 0),
            QColor(0, 255, 0), QColor(0, 0, 255), QColor(255, 255, 0),
            QColor(255, 0, 255), QColor(0, 255, 255), QColor(255, 165, 0),
            QColor(128, 0, 128), QColor(0, 128, 128), QColor(128, 128, 0)
        ]
        
        # Multi-page support
        self.pages: List[Page] = [Page(name="Untitled")]
        self.current_page_index = 0
        
        # Create canvas
        self.canvas = InkCanvas()
        self.canvas.load_page_data(self.pages[0])
        self.setCentralWidget(self.canvas)
        
        # Tool Action Group (Mutually Exclusive)
        self.tool_group = QActionGroup(self)
        self.tool_group.setExclusive(True)
        self.tool_group.triggered.connect(self._on_tool_group_triggered)
        
        # Setup UI
        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Setup UI
        self._create_main_toolbar()
        self._create_tool_toolbar()
        self._create_pen_toolbar()
        self._create_shape_toolbar()
        self._create_settings_toolbar()
        self._create_action_toolbar()
        
        # Page controls in status bar
        self._create_status_bar_controls()
        
        # Update page indicator
        self._update_page_indicator()
        
        # Apply professional theme
        self._apply_professional_theme()
        
        # Settings (Persistence)
        # Settings (Persistence)
        # Using a new key to force reset of layout to match the requested "Legacy" look
        self.settings = QSettings("ScrbleInk", "Pro_Legacy")
        self._restore_state()

    def closeEvent(self, event):
        """Save state on close"""
        # Auto-save before closing
        if hasattr(self, 'active_file_path') and self.active_file_path:
             self._save_file(silent=True)
             
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        super().closeEvent(event)
        
    def _restore_state(self):
        """Restore window state"""
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        state = self.settings.value("windowState")
        if state:
            self.restoreState(state)

    def resizeEvent(self, event):
        """Handle responsive layout"""
        is_compact = self.width() < 1000
        
        # Toggle visibility of labels
        if hasattr(self, 'lbl_width'): self.lbl_width.setVisible(not is_compact)
        if hasattr(self, 'lbl_smooth'): self.lbl_smooth.setVisible(not is_compact)
        if hasattr(self, 'lbl_colors'): self.lbl_colors.setVisible(not is_compact)
        if hasattr(self, 'lbl_bg'): self.lbl_bg.setVisible(not is_compact)
        
        super().resizeEvent(event)
        
        # Responsive Toolbar Layout for Actions
        if hasattr(self, 'action_toolbar'):
             # Check if we should force a new line
             should_break = self.width() < 1100
             
             # We use insertToolBarBreak to force a new line
             # Note: insertToolBarBreak(toolbar) inserts a break BEFORE the specified toolbar
             
             # To robustly handle this without "removeToolBarBreak" (which doesn't exist directly in older Qt or requires finding the break),
             # we can just re-add the toolbar with/without a break.
             
             # Simpler approach: Check if it's already on a new line?
             # Actually, simpler hack for PyQt: 
             # We can use addToolBarBreak if it's the last one, or insertToolBarBreak.
             # But removing is hard.
             
             # Strategy: maintain a state
             if not hasattr(self, '_action_toolbar_broken'):
                 self._action_toolbar_broken = False
                 
             if should_break and not self._action_toolbar_broken:
                 self.insertToolBarBreak(self.action_toolbar)
                 self._action_toolbar_broken = True
             elif not should_break and self._action_toolbar_broken:
                 # To "remove" a break, we sadly have to remove the toolbar and re-add it 
                 # or use clean-up. 
                 self.removeToolBar(self.action_toolbar)
                 self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.action_toolbar)
                 self._action_toolbar_broken = False
    
    def _create_main_toolbar(self):
        """Create main toolbar with file operations"""
        toolbar = QToolBar("Main")
        toolbar.setObjectName("MainToolbar_v2") # Renamed to reset state/layout
        toolbar.setMovable(True)
        toolbar.setFloatable(True)
        toolbar.setAllowedAreas(Qt.ToolBarArea.AllToolBarAreas)
        toolbar.setIconSize(QSize(20, 20))
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon) # Show text
        self.addToolBar(Qt.ToolBarArea.RightToolBarArea, toolbar)
        
        # Close / Exit (First item for visibility)
        close_action = QAction("❌ Close", self)
        close_action.setToolTip("Close - Exit Whiteboard")
        close_action.triggered.connect(self.close)
        toolbar.addAction(close_action)
        
        
        # Export PDF (Requested by user below Close)
        export_pdf_action = QAction("📄 PDF", self)
        export_pdf_action.setToolTip("Export as PDF (All Pages)")
        export_pdf_action.triggered.connect(self._export_pdf_direct)
        toolbar.addAction(export_pdf_action)
        
        toolbar.addSeparator()
        
        
        # Menu (Removed as per user request)
        # menu_btn = QAction("☰", self)
        # menu_btn.triggered.connect(self._show_menu)
        # toolbar.addAction(menu_btn)
        
        # New page
        new_action = QAction("📄", self)
        new_action.setToolTip("New Page - Create a new blank page")
        new_action.triggered.connect(self._add_page)
        toolbar.addAction(new_action)
        
        # Open
        open_action = QAction("📂", self)
        open_action.setToolTip("Open File - Open an existing .scrble or .json file")
        open_action.triggered.connect(self._open_file)
        toolbar.addAction(open_action)
        
        # Save
        save_action = QAction("💾", self)
        save_action.setToolTip("Save File (Ctrl+S) - Save current document")
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._save_file)
        toolbar.addAction(save_action)
        
        # Export
        export_action = QAction("📤", self)
        export_action.setToolTip("Export - Export current page as Image or PDF")
        export_action.triggered.connect(self._export_image)
        toolbar.addAction(export_action)


        toolbar.addSeparator()
        
        # Undo
        undo_action = QAction("↶", self)
        undo_action.setToolTip("Undo (Ctrl+Z) - Revert last action")
        undo_action.setShortcut("Ctrl+Z")
        undo_action.setShortcutContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        undo_action.triggered.connect(self.canvas.undo)
        toolbar.addAction(undo_action)
        
        # Redo
        redo_action = QAction("↷", self)
        redo_action.setToolTip("Redo (Ctrl+Y) - Reapply undone action")
        redo_action.setShortcut("Ctrl+Y")
        redo_action.setShortcutContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        redo_action.triggered.connect(self.canvas.redo)
        toolbar.addAction(redo_action)
        
        toolbar.addSeparator()
        
        toolbar.addSeparator()
        
        # Clear
        clear_action = QAction("🗑", self)
        clear_action.setToolTip("Clear Canvas - Delete all content on current page")
        clear_action.triggered.connect(self._clear_canvas)
        toolbar.addAction(clear_action)
    
    def _create_status_bar_controls(self):
        """Create page controls in status bar"""
        # Page indicator
        self.page_label = QLabel()
        self.page_label.setStyleSheet(f"font-size: {ThemeConfig.FONT_SIZE_MAIN}pt; font-weight: bold; margin: 0 5px;")
        
        # Navigation buttons
        prev_btn = QPushButton("◄")
        prev_btn.setFixedSize(20, 20)
        prev_btn.setToolTip("Previous Page - Go to previous page")
        prev_btn.clicked.connect(self._prev_page)
        
        next_btn = QPushButton("►")
        next_btn.setFixedSize(20, 20)
        next_btn.setToolTip("Next Page - Go to next page")
        next_btn.clicked.connect(self._next_page)
        
        # Add to status bar
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 20, 0)
        layout.setSpacing(10)
        
        layout.addWidget(prev_btn)
        layout.addWidget(self.page_label)
        layout.addWidget(next_btn)
        
        self.status_bar.addPermanentWidget(container)
    
    def _create_tool_toolbar(self):
        """Create toolbar for drawing tools"""
        toolbar = QToolBar("Tools")
        toolbar.setObjectName("ToolsToolbar")
        toolbar.setMovable(True)
        toolbar.setFloatable(True)
        toolbar.setAllowedAreas(Qt.ToolBarArea.AllToolBarAreas)
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, toolbar)
        
        # Select tool
        select_action = QAction("👆", self)
        select_action.setToolTip("Select - Click to select/move items")
        select_action.setCheckable(True)
        select_action.setData(ToolType.SELECT)
        select_action.setActionGroup(self.tool_group)
        toolbar.addAction(select_action)
        self.select_action = select_action
        

        
        toolbar.addSeparator()
        
        # Pen tools
        pen_action = QAction("🖊", self)
        pen_action.setToolTip("Pen - Standard digital ink pen")
        pen_action.setCheckable(True)
        pen_action.setChecked(True)
        pen_action.setData(ToolType.PEN)
        pen_action.setActionGroup(self.tool_group)
        toolbar.addAction(pen_action)
        self.pen_action = pen_action
        
        ballpoint_action = QAction("🖊", self)
        ballpoint_action.setToolTip("Ballpoint - Consistent width pen")
        ballpoint_action.setCheckable(True)
        ballpoint_action.setData(ToolType.BALLPOINT)
        ballpoint_action.setActionGroup(self.tool_group)
        toolbar.addAction(ballpoint_action)
        self.ballpoint_action = ballpoint_action
        
        pencil_action = QAction("✏", self)
        pencil_action.setToolTip("Pencil - Texture and transparency like a real pencil")
        pencil_action.setCheckable(True)
        pencil_action.setData(ToolType.PENCIL)
        pencil_action.setActionGroup(self.tool_group)
        toolbar.addAction(pencil_action)
        self.pencil_action = pencil_action
        
        marker_action = QAction("🖍", self)
        marker_action.setToolTip("Marker - Broad, flat-tip marker")
        marker_action.setCheckable(True)
        marker_action.setData(ToolType.MARKER)
        marker_action.setActionGroup(self.tool_group)
        toolbar.addAction(marker_action)
        self.marker_action = marker_action
        
        highlighter_action = QAction("🖌️", self)
        highlighter_action.setToolTip("Highlighter - Transparent overlay for highlighting")
        highlighter_action.setCheckable(True)
        highlighter_action.setData(ToolType.HIGHLIGHTER)
        highlighter_action.setActionGroup(self.tool_group)
        toolbar.addAction(highlighter_action)
        self.highlighter_action = highlighter_action
        
        toolbar.addSeparator()
        
        # Erasers
        eraser_action = QAction("🧽", self)
        eraser_action.setToolTip("Eraser - Manual eraser")
        eraser_action.setCheckable(True)
        eraser_action.setData(ToolType.ERASER)
        eraser_action.setActionGroup(self.tool_group)
        toolbar.addAction(eraser_action)
        self.eraser_action = eraser_action
        
        stroke_eraser_action = QAction("✂", self)
        stroke_eraser_action.setToolTip("Stroke Eraser - Remove entire strokes")
        stroke_eraser_action.setCheckable(True)
        stroke_eraser_action.setData(ToolType.STROKE_ERASER)
        stroke_eraser_action.setActionGroup(self.tool_group)
        toolbar.addAction(stroke_eraser_action)
        self.stroke_eraser_action = stroke_eraser_action
        
        # REMOVED: self.tool_actions list (handled by group)
    
    def _create_pen_toolbar(self):
        """Create pen settings toolbar"""
        toolbar = QToolBar("Pen Settings")
        toolbar.setObjectName("PenSettingsToolbar")
        toolbar.setMovable(True)
        toolbar.setFloatable(True)
        toolbar.setAllowedAreas(Qt.ToolBarArea.AllToolBarAreas)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)
        
        # Width slider
        toolbar.addWidget(QLabel("Width:"))
        width_slider = QSlider(Qt.Orientation.Horizontal)
        width_slider.setMinimum(1)
        width_slider.setMaximum(50)
        width_slider.setValue(3)
        width_slider.setMaximumWidth(200)
        width_slider.valueChanged.connect(self._on_width_changed)
        toolbar.addWidget(width_slider)
        self.width_slider = width_slider
        
        self.width_label = QLabel("3px")
        self.width_label.setMinimumWidth(50)
        toolbar.addWidget(self.width_label)
        
        toolbar.addSeparator()
        
        # Smoothing
        toolbar.addWidget(QLabel("  Smooth:"))
        smooth_slider = QSlider(Qt.Orientation.Horizontal)
        smooth_slider.setMinimum(0)
        smooth_slider.setMaximum(5)
        smooth_slider.setValue(2)
        smooth_slider.setMaximumWidth(150)
        smooth_slider.valueChanged.connect(lambda v: setattr(self.canvas, 'smoothing_level', v))
        toolbar.addWidget(smooth_slider)
        
        toolbar.addSeparator()
        
        # Color palette
        self.lbl_colors = QLabel("  Colors: ")
        toolbar.addWidget(self.lbl_colors)
        for color in self.color_palette[:8]:
            btn = QPushButton()
            btn.setFixedSize(24, 24)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color.name()};
                    border: 2px solid #555;
                    border-radius: 15px;
                }}
                QPushButton:hover {{
                    border: 2px solid #fff;
                }}
            """)
            btn.clicked.connect(lambda checked, c=color: self.canvas.set_color(c))
            toolbar.addWidget(btn)
        
        # Custom color
        custom_color_btn = QPushButton("⊕")
        custom_color_btn.setToolTip("Custom Color")
        custom_color_btn.clicked.connect(self._pick_custom_color)
        toolbar.addWidget(custom_color_btn)
    
    def _create_shape_toolbar(self):
        """Create shapes toolbar"""
        toolbar = QToolBar("Shapes")
        toolbar.setObjectName("ShapesToolbar")
        toolbar.setMovable(True)
        toolbar.setFloatable(True)
        toolbar.setAllowedAreas(Qt.ToolBarArea.AllToolBarAreas)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)
        
        # Line
        line_action = QAction("─", self)
        line_action.setToolTip("Line - Draw straight lines")
        line_action.setCheckable(True)
        line_action.setData(ToolType.LINE)
        line_action.setActionGroup(self.tool_group)
        toolbar.addAction(line_action)
        self.line_action = line_action
        
        # Rectangle
        rect_action = QAction("□", self)
        rect_action.setToolTip("Rectangle - Draw rectangles")
        rect_action.setCheckable(True)
        rect_action.setData(ToolType.RECTANGLE)
        rect_action.setActionGroup(self.tool_group)
        toolbar.addAction(rect_action)
        self.rect_action = rect_action
        
        # Circle
        circle_action = QAction("○", self)
        circle_action.setToolTip("Circle - Draw ellipses/circles")
        circle_action.setCheckable(True)
        circle_action.setData(ToolType.CIRCLE)
        circle_action.setActionGroup(self.tool_group)
        toolbar.addAction(circle_action)
        self.circle_action = circle_action
        
        # Arrow
        arrow_action = QAction("➔", self)
        arrow_action.setToolTip("Arrow - Draw arrows")
        arrow_action.setCheckable(True)
        arrow_action.setData(ToolType.ARROW)
        arrow_action.setActionGroup(self.tool_group)
        toolbar.addAction(arrow_action)
        self.arrow_action = arrow_action
        
        # Double Arrow
        double_arrow_action = QAction("↔", self)
        double_arrow_action.setToolTip("Double Arrow - Draw double-ended arrows")
        double_arrow_action.setCheckable(True)
        double_arrow_action.setData(ToolType.DOUBLE_ARROW)
        double_arrow_action.setActionGroup(self.tool_group)
        toolbar.addAction(double_arrow_action)
        self.double_arrow_action = double_arrow_action
        
        toolbar.addSeparator()
        
        # Removed self.tool_actions update
    
    def _create_settings_toolbar(self):
        """Create settings toolbar"""
        toolbar = QToolBar("Settings")
        toolbar.setObjectName("SettingsToolbar")
        toolbar.setMovable(True)
        toolbar.setFloatable(True)
        toolbar.setAllowedAreas(Qt.ToolBarArea.AllToolBarAreas)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)
        
        # Background type
        self.lbl_bg = QLabel("  Background: ")
        toolbar.addWidget(self.lbl_bg)
        bg_combo = QComboBox()
        bg_combo.addItems(["Dots", "Grid", "Lines", "Lines + Margin", "Graph", "Plain"])
        bg_combo.currentIndexChanged.connect(self._change_background)
        toolbar.addWidget(bg_combo)
        
        # Background color
        bg_color_btn = QPushButton("BG Color")
        bg_color_btn.clicked.connect(self._pick_background_color)
        toolbar.addWidget(bg_color_btn)
        
        toolbar.addSeparator()
        
        # Ruler
        ruler_checkbox = QCheckBox("Ruler")
        ruler_checkbox.stateChanged.connect(lambda state: self._toggle_ruler(state == Qt.CheckState.Checked))
        toolbar.addWidget(ruler_checkbox)
        
        toolbar.addSeparator()
        
        # Add image - MOVED to Action Toolbar
        
    def _create_action_toolbar(self):
        """Create actions toolbar (Insert to Note, Image)"""
        toolbar = QToolBar("Actions")
        toolbar.setObjectName("ActionsToolbar")
        toolbar.setMovable(True)
        toolbar.setFloatable(True)
        toolbar.setAllowedAreas(Qt.ToolBarArea.AllToolBarAreas)
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        
        # Force handle style directly on this toolbar to ensure visibility
        # The Base64 string is the 6-dot gripe handle
        toolbar.setStyleSheet("""
            QToolBar::handle {
                background-image: url("assets/handle.svg");
                background-position: center;
                background-repeat: no-repeat;
                width: 12px;
                margin: 2px;
            }
            QToolBar::handle:horizontal {
                width: 12px;
                background-position: center;
                margin-left: 2px;
                margin-right: 2px;
            }
            QToolBar::handle:vertical {
                height: 12px;
                background-position: center;
                margin-top: 2px;
                margin-bottom: 2px;
            }
        """)
        
        # We add it to Top, but we might want to force it to a new row if we could
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)
        self.action_toolbar = toolbar # Store reference
        
        # Insert to Note
        # Using Icon+Text for high visibility as requested
        save_action = QAction("✔️ Insert to Note", self)
        save_action.setToolTip("Insert to Note - Instantly insert drawing into Note App")
        save_action.triggered.connect(self._quick_save_to_note)
        
        # Style hint: The user showed a purple checkmark. We can try to style it if it was a button, 
        # but for QAction within QToolBar, we rely on the icon.
        # We'll stick to standard QAction for now, but ensure Text is visible.
        toolbar.addAction(save_action)
        
        toolbar.addSeparator()
        
        # Image Action
        img_action = QAction("📷 Image", self)
        img_action.setToolTip("Add Image - Import an image to the canvas")
        img_action.triggered.connect(self._add_image)
        toolbar.addAction(img_action)

    def _on_tool_group_triggered(self, action):
        """Handle tool selection from QActionGroup"""
        tool = action.data()
        if tool:
            self._update_ui_for_tool(tool)
            self.canvas.set_tool(tool)

    def _update_ui_for_tool(self, tool: ToolType):
        """Update UI elements (sliders) for the selected tool"""
        self.width_slider.blockSignals(True)
        if tool == ToolType.ERASER:
            self.width_slider.setValue(int(self.canvas.eraser_width))
            self.width_label.setText(f"{int(self.canvas.eraser_width)}px")
        elif tool in self.canvas.pen_styles:
            self.width_slider.setValue(int(self.canvas.pen_styles[tool]['width']))
            self.width_label.setText(f"{int(self.canvas.pen_styles[tool]['width'])}px")
        self.width_slider.blockSignals(False)

    def _set_tool(self, tool: ToolType):
        """Set active tool programmatically"""
        # Find action for tool and check it - this triggers _on_tool_group_triggered
        for action in self.tool_group.actions():
            if action.data() == tool:
                action.setChecked(True)
                break
    
    def _on_width_changed(self, value):
        """Handle width slider change"""
        if self.canvas.current_tool == ToolType.ERASER:
             self.canvas.eraser_width = value
        else:
             self.canvas.set_pen_width(value)
        self.width_label.setText(f"{value}px")
        # Trigger update to resize cursor if in eraser mode
        self.canvas.update()
    
    def _pick_custom_color(self):
        """Open color picker"""
        color = QColorDialog.getColor()
        if color.isValid():
            self.canvas.set_color(color)
    
    def _pick_background_color(self):
        """Pick background color"""
        color = QColorDialog.getColor(self.canvas.background_color)
        if color.isValid():
            self.canvas.set_background_color(color)
    
    def _change_background(self, index):
        """Change background type"""
        bg_types = [BackgroundType.DOTS, BackgroundType.GRID, 
                   BackgroundType.LINES, BackgroundType.LINES_WITH_MARGIN, 
                   BackgroundType.GRAPH, BackgroundType.PLAIN]
        if 0 <= index < len(bg_types):
            self.canvas.set_background_type(bg_types[index])
    
    def _toggle_ruler(self, enabled):
        """Toggle ruler"""
        self.canvas.show_ruler = enabled
        self.canvas.update()
    
    def _add_image(self):
        """Add image to canvas"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "", 
            "Images (*.png *.jpg *.jpeg *.bmp *.gif *.svg)"
        )
        if filename:
            self.canvas.add_image(filename)
    
    def _update_page_indicator(self):
        """Update page indicator"""
        page = self.pages[self.current_page_index]
        
        # Extract folder name from active path
        folder_name = ""
        if hasattr(self, 'active_file_path') and self.active_file_path:
            import os
            try:
                # Assuming path is .../Folder/whiteboard.json
                # direct parent is the folder
                folder_name = os.path.basename(os.path.dirname(self.active_file_path))
                folder_name = f"[{folder_name}] - "
            except:
                pass
                
        # Prepare page name text
        page_text = ""
        if page.name and page.name != "Untitled":
            page_text = f" - {page.name}"
            
        self.page_label.setText(
            f"{folder_name}Page {self.current_page_index + 1} / {len(self.pages)}{page_text}"
        )
    
    def _prev_page(self):
        """Previous page"""
        if self.current_page_index > 0:
            self.canvas.save_page_data(self.pages[self.current_page_index])
            self.current_page_index -= 1
            self.canvas.load_page_data(self.pages[self.current_page_index])
            self._update_page_indicator()
    
    def _next_page(self):
        """Next page"""
        if self.current_page_index < len(self.pages) - 1:
            self.canvas.save_page_data(self.pages[self.current_page_index])
            self.current_page_index += 1
            self.canvas.load_page_data(self.pages[self.current_page_index])
            self._update_page_indicator()
    
    def _add_page(self):
        """Add new page"""
        self.canvas.save_page_data(self.pages[self.current_page_index])
        new_page = Page(name=f"Page {len(self.pages) + 1}")
        self.pages.append(new_page)
        self.current_page_index = len(self.pages) - 1
        self.canvas.load_page_data(new_page)
        self._update_page_indicator()
    
    def _clear_canvas(self):
        """Clear canvas"""
        dlg = ModernMessageBox(
            'Clear Canvas',
            'Clear current page? This cannot be undone.',
            QMessageBox.Yes | QMessageBox.No,
            self
        )
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.canvas.clear_canvas()
    
    def _save_file(self, silent=False):
        """Save document"""
        filename = None
        
        # IMAGE EDIT MODE: Overwrite existing image logic
        if hasattr(self, 'image_edit_mode') and self.image_edit_mode:
            if hasattr(self, 'image_edit_path') and self.image_edit_path:
                try:
                    # Capture the full canvas
                    # We use grab() which takes a screenshot of the widget
                    # This includes background + strokes + images
                    pixmap = self.canvas.grab()
                    if pixmap.save(self.image_edit_path):
                         ModernMessageBox("Success", "Image updated successfully!", QMessageBox.StandardButton.Ok, self).exec()
                         return
                    else:
                        raise Exception("Failed to write image file.")
                except Exception as e:
                     ModernMessageBox("Error", f"Failed to update image: {e}", QMessageBox.StandardButton.Ok, self).exec()
                     return

        # Normal Save Logic
        if hasattr(self, 'active_file_path') and self.active_file_path:
             filename = self.active_file_path
        else:
            if silent: return # Cannot save silently if no path
            filename, _ = QFileDialog.getSaveFileName(
                self, "Save Document", "", 
                "Scrble Pro Files (*.scrble);;JSON Files (*.json)"
            )
        
        if filename:
            self.active_file_path = filename

            self.canvas.save_page_data(self.pages[self.current_page_index])
            data = {
                'version': '2.0',
                'pages': [page.to_dict() for page in self.pages],
                'current_page': self.current_page_index
            }
            try:
                import tempfile
                import os
                
                temp_fd, temp_path = tempfile.mkstemp(dir=os.path.dirname(filename), suffix=".tmp")
                try:
                    with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2)
                    os.replace(temp_path, filename)
                except Exception as e:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    raise e
                    
                if not silent:
                    ModernMessageBox("Success", "Document saved!", QMessageBox.Ok, self).exec()
            except Exception as e:
                # Fallback to printer if logger not yet imported (it should be)
                if not silent:
                    ModernMessageBox("Error", f"Failed to save: {e}", QMessageBox.Ok, self).exec()
                print(f"Save failed: {e}")
    
    def _open_file(self):
        """Open a file"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Open File", "", 
            "Scrble Files (*.scrble);;JSON Files (*.json)"
        )
        if filename:
            self._load_file_path(filename)

    def _load_file_path(self, filename):
        """Load a file from specific path"""
        try:
            import json
            with open(filename, 'r') as f:
                data = json.load(f)
                
            self.pages = [Page.from_dict(p) for p in data['pages']]
            self.current_page_index = data.get('current_page', 0)
            self.canvas.load_page_data(self.pages[self.current_page_index])
            
            # Logic: If last page has strokes, add new one?
            if self.pages:
                last_page = self.pages[-1]
                if last_page.strokes or last_page.images or last_page.shapes:
                    self._add_page()
            
            self._update_page_indicator()
            self.active_file_path = filename # update active path
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            if self.isVisible():
                 ModernMessageBox("Error", f"Failed to open file:\n{str(e)}", QMessageBox.Ok, self).exec()

    def _export_pdf_direct(self):
        """Export all pages to PDF directly with Table of Contents"""
        
        # Determine default filename from folder name
        default_name = "Whiteboard Export"
        if hasattr(self, 'active_file_path') and self.active_file_path:
            import os
            try:
                # .../Folder/whiteboard.json -> Folder
                folder_name = os.path.basename(os.path.dirname(self.active_file_path))
                if folder_name:
                    default_name = folder_name
            except:
                pass
                
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export to PDF", default_name, 
            "PDF Document (*.pdf)"
        )
        
        if filename:
            if not filename.lower().endswith('.pdf'):
                filename += ".pdf"
                
            try:
                from PySide6.QtGui import QPdfWriter, QPageLayout, QPageSize, QFont, QPen
                from PySide6.QtCore import QMarginsF, QRectF
                
                writer = QPdfWriter(filename)
                writer.setPageSize(QPageSize(QPageSize.A4))
                writer.setResolution(300) # High quality (300 DPI)
                
                painter = QPainter(writer)
                
                # --- Generate TOC Page ---
                # A4 at 300 DPI is approx 2480 x 3508 pixels
                # We need to scale our drawing when using logical coords?
                # QPdfWriter uses logical dots (usually 1/72 inch)? No, setResolution(300) makes logical units 1/300 inch.
                # Standard A4 is 8.27 x 11.69 inches.
                # Width = 8.27 * 300 = 2481 px.
                
                # Title
                title_font = QFont("Arial", 24, QFont.Bold)
                painter.setFont(title_font)
                painter.drawText(100, 200, f"Table of Contents - {default_name}")
                
                # List Pages
                item_font = QFont("Arial", 14)
                painter.setFont(item_font)
                y_pos = 400
                
                for i, page in enumerate(self.pages):
                    page_name = page.name if page.name else "Untitled"
                    # Format: 1. Page Name .......................... Page X
                    # Simple list for now
                    text = f"{i+1}. {page_name}"
                    painter.drawText(100, y_pos, text)
                    
                    # Add simple "Link" visualization (functionality requires QPdfWriter.setLink which is complex via Painter)
                    # We just list them for now as requested "top toc of the notes name toc"
                    y_pos += 80
                
                # --- Render Pages ---
                for i, page_data in enumerate(self.pages):
                    writer.newPage()
                    
                    # Save current state if needed
                    if i == self.current_page_index:
                         self.canvas.save_page_data(self.pages[i])
                    
                    # Load page
                    self.canvas.load_page_data(self.pages[i])
                    
                    # Render Content
                    # We need to scale the canvas content to fit the PDF page
                    # Canvas size might be screen relative (e.g. 1920x1080)
                    # PDF Page is ~2480x3508
                    
                    canvas_size = self.canvas.size()
                    page_rect = writer.pageLayout().paintRectPixels(writer.resolution())
                    
                    # Calculate scale to Fit Width (maintain aspect ratio)
                    scale_w = page_rect.width() / canvas_size.width()
                    scale_h = page_rect.height() / canvas_size.height() 
                    scale = min(scale_w, scale_h) * 0.95 # 95% to leave margin
                    
                    painter.save()
                    # Center render
                    tx = (page_rect.width() - (canvas_size.width() * scale)) / 2
                    ty = (page_rect.height() - (canvas_size.height() * scale)) / 2
                    painter.translate(tx, ty)
                    painter.scale(scale, scale)
                    
                    self.canvas.render_to_painter(painter)
                    painter.restore()
                    
                    # Page Number Footer
                    painter.save()
                    footer_font = QFont("Arial", 10)
                    painter.setFont(footer_font)
                    painter.drawText(QRectF(0, page_rect.height() - 100, page_rect.width(), 50), 
                                   Qt.AlignmentFlag.AlignCenter, f"Page {i+1}")
                    painter.restore()

                painter.end()
                
                # Restore original page
                self.canvas.load_page_data(self.pages[self.current_page_index])
                
                ModernMessageBox("Success", f"PDF exported with {len(self.pages)} pages + TOC!", QMessageBox.Ok, self).exec()
            except Exception as e:
                import traceback
                traceback.print_exc()
                ModernMessageBox("Error", f"PDF Export failed: {e}", QMessageBox.Ok, self).exec()

    def _export_image(self):
        """Export as image or PDF"""
        default_name = self.windowTitle() if self.windowTitle() else "whiteboard"
        # Sanitize filename
        default_name = "".join(c for c in default_name if c.isalnum() or c in (' ', '-', '_')).strip()
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Image", default_name, 
            "PNG Image (*.png);;JPEG Image (*.jpg);;PDF Document (*.pdf)"
        )
        if filename:
            if filename.lower().endswith('.pdf'):
                # Redirect to specific handler if they chose PDF here too
                # For now just use the existing logic or copy it.
                # Since we added _export_pdf_direct, let's keep _export_image focused on image but keep legacy support
                pass # (existing logic below)
            # ... existing logic
            if filename.lower().endswith('.pdf'):
                 # ... existing pdf logic ...
                 pass
            if filename.lower().endswith('.pdf'):
                try:
                    from PySide6.QtGui import QPdfWriter, QPageLayout, QPageSize
                    from PySide6.QtCore import QMarginsF
                    
                    writer = QPdfWriter(filename)
                    writer.setPageSize(QPageSize(QPageSize.A4))
                    writer.setResolution(300) # High quality
                    
                    painter = QPainter(writer)
                    
                    # Iterate through all pages
                    for i, page_data in enumerate(self.pages):
                        if i > 0:
                            writer.newPage()
                        
                        # Save current state logic
                        if i == self.current_page_index:
                             self.canvas.save_page_data(self.pages[i])
                        
                        # Load and render
                        self.canvas.load_page_data(self.pages[i])
                        self.canvas.render(painter)
                        
                    painter.end()
                    
                    # Restore original page
                    self.canvas.load_page_data(self.pages[self.current_page_index])
                    
                    ModernMessageBox("Success", f"PDF exported with {len(self.pages)} pages!", QMessageBox.Ok, self).exec()
                except Exception as e:
                    ModernMessageBox("Error", f"PDF Export failed: {e}", QMessageBox.Ok, self).exec()
            else:
                pixmap = self.canvas.grab()
                pixmap.save(filename)
                ModernMessageBox("Success", "Image exported!", QMessageBox.Ok, self).exec()




    
    def _quick_save_to_note(self):
        """Save current view to temp file and signal parent process"""
        import tempfile
        import os
        
        # Create a temp file path
        # We use a fixed name pattern or random? 
        # Random is safer to avoid conflicts/locking, but let's just make a new one.
        
        # IMAGE EDIT MODE: Overwrite existing image logic
        if hasattr(self, 'image_edit_mode') and self.image_edit_mode:
            if hasattr(self, 'image_edit_path') and self.image_edit_path:
                try:
                    # Capture the full canvas
                    pixmap = self.canvas.grab()
                    if pixmap.save(self.image_edit_path):
                         # ModernMessageBox("Success", "Image updated!", QMessageBox.Ok, self).exec()
                         # Just print success or maybe close?
                         # Usually checkmark means "Done". 
                         # Let's close automatically for seamless workflow?
                         # User said "see now properly openting ... try to save updated image".
                         # Let's start with just saving.
                         print(f"IPC_UPDATE_IMAGE:{self.image_edit_path}", flush=True) # Signal update if needed
                         # self.close() # Optional: Auto-close? User didn't explicitly ask, but "Done" implies it.
                         # Let's KEEP OPEN for now, user can close.
                         return
                    else:
                        print(f"Error saving overwrite: Failed to write {self.image_edit_path}")
                        return
                except Exception as e:
                     print(f"Error saving overwrite: {e}")
                     return

        
        try:
            fd, path = tempfile.mkstemp(suffix='.png', prefix='scrble_note_')
            os.close(fd)
            
            # Save the canvas to this path
            # Use high quality export (3x scale)
            pixmap = QPixmap.fromImage(self.canvas.get_high_quality_image(3.0))
            pixmap.save(path, 'PNG')
            
            # Signal parent process via stdout
            # Format: 'IPC_SAVE_IMAGE:<path>'
            print(f"IPC_SAVE_IMAGE:{path}", flush=True)
            
            # Optional: Feedback
            # ModernMessageBox("Saved", "Drawing sent to Note App!", QMessageBox.Ok, self).exec()
            # Or just flash? Let's just give subtle feedback or none if it's meant to be fast.
            # User asked "see when user clcik save then add that image"
            
        except Exception as e:
            print(f"Error saving temp: {e}")

    
    def _show_menu(self):
        """Show menu"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2d2d2d;
                color: white;
                border: 1px solid #555;
            }
            QMenu::item:selected {
                background-color: #0d7377;
            }
        """)
        
        about_action = menu.addAction("About Professional Scrble Ink")
        shortcuts_action = menu.addAction("Keyboard Shortcuts")
        menu.addSeparator()
        help_action = menu.addAction("Help & Documentation")
        
        action = menu.exec_(self.mapToGlobal(QPoint(10, 60)))
        
        if action == about_action:
            self._show_about()
        elif action == shortcuts_action:
            self._show_shortcuts()
    
    def _show_about(self):
        """Show about dialog"""
        ModernMessageBox(
            "About",
            "Professional Scrble Ink v2.0\n\n"
            "Industry-level digital whiteboard with:\n"
            "• Multiple pen types (pen, ballpoint, pencil, marker)\n"
            "• Professional eraser modes\n"
            "• Geometric shapes with fill options\n"
            "• Image support\n"
            "• Multiple background themes\n"
            "• Ruler and grid overlays\n"
            "• Multi-page documents\n"
            "• Pressure-sensitive drawing\n"
            "• Smooth stroke rendering\n\n"
            "Created with PySide6",
            QMessageBox.Ok,
            self
        ).exec()
    
    def _show_shortcuts(self):
        """Show keyboard shortcuts"""
        ModernMessageBox(
            "Keyboard Shortcuts",
            "Ctrl+Z: Undo\n"
            "Ctrl+Y: Redo\n"
            "Ctrl+S: Save\n"
            "Ctrl+Wheel: Zoom\n"
            "Ctrl+Drag or Middle Mouse: Pan\n"
            "Tab: Cycle through tools\n"
            "[ / ]: Decrease/Increase brush size\n"
            "Space+Drag: Pan canvas",
            QMessageBox.Ok,
            self
        ).exec()
    
    def _apply_professional_theme(self):
        """Apply professional dark theme"""
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {ThemeConfig.BG_DARKER};
            }}
            QToolBar {{
                background-color: {ThemeConfig.BG_DARK};
                border-bottom: 1px solid {ThemeConfig.BORDER};
                spacing: 4px;
                padding: 2px;
            }}
            QToolBar::handle {{
                background-image: url("assets/handle.svg");
                background-position: center;
                background-repeat: no-repeat;
                width: 12px;
                margin: 2px;
            }}
            QToolBar::handle:horizontal {{
                width: 12px;
                background-position: center;
                margin-left: 2px;
                margin-right: 2px;
            }}
            QToolBar::handle:vertical {{
                height: 12px;
                background-position: center;
                margin-top: 2px;
                margin-bottom: 2px;
            }}
            QToolButton {{
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: {ThemeConfig.RADIUS}px;
                padding: 2px;
                color: {ThemeConfig.TEXT_SECONDARY};
                font-size: 12pt;
            }}
            QToolButton:hover {{
                background-color: {ThemeConfig.BORDER};
                color: {ThemeConfig.TEXT_PRIMARY};
                border: 1px solid {ThemeConfig.ACCENT_HOVER};
            }}
            QToolButton:checked {{
                background-color: {ThemeConfig.ACCENT}20;
                color: {ThemeConfig.ACCENT};
                border: 1px solid {ThemeConfig.ACCENT};
            }}
            QPushButton {{
                background-color: {ThemeConfig.BG_LIGHT};
                color: {ThemeConfig.TEXT_PRIMARY};
                border: 1px solid {ThemeConfig.BORDER};
                border-radius: {ThemeConfig.RADIUS}px;
                padding: 2px 8px;
                font-family: {ThemeConfig.FONT_FAMILY};
            }}
            QPushButton:hover {{
                background-color: {ThemeConfig.BG_LIGHT}cc;
                border: 1px solid {ThemeConfig.ACCENT};
            }}
            QLabel {{
                color: {ThemeConfig.TEXT_PRIMARY};
                font-family: {ThemeConfig.FONT_FAMILY};
            }}
            QSlider::groove:horizontal {{
                background: {ThemeConfig.BG_LIGHT};
                height: 6px;
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {ThemeConfig.ACCENT};
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {ThemeConfig.ACCENT_HOVER};
            }}
            QComboBox {{
                background-color: {ThemeConfig.BG_LIGHT};
                color: {ThemeConfig.TEXT_PRIMARY};
                border: 1px solid {ThemeConfig.BORDER};
                border-radius: {ThemeConfig.RADIUS}px;
                padding: 6px 10px;
            }}
            QComboBox:hover {{
                border: 1px solid {ThemeConfig.ACCENT};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QCheckBox {{
                color: {ThemeConfig.TEXT_PRIMARY};
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 1px solid {ThemeConfig.TEXT_SECONDARY};
                border-radius: 4px;
                background: transparent;
            }}
            QCheckBox::indicator:checked {{
                background: {ThemeConfig.ACCENT};
                border-color: {ThemeConfig.ACCENT};
            }}
            QToolTip {{
                color: {ThemeConfig.TEXT_PRIMARY};
                background-color: {ThemeConfig.BG_DARK};
                border: 1px solid {ThemeConfig.BORDER};
            }}
            QMenu {{
                background-color: {ThemeConfig.BG_DARK};
                border: 1px solid {ThemeConfig.BORDER};
                padding: 5px;
            }}
            QMenu::item {{
                padding: 8px 25px;
                border-radius: 4px;
                color: {ThemeConfig.TEXT_PRIMARY};
            }}
            QMenu::item:selected {{
                background-color: {ThemeConfig.ACCENT};
                color: {ThemeConfig.BG_DARKER};
            }}
            QScrollBar:vertical {{
                border: none;
                background: {ThemeConfig.BG_DARK};
                width: 10px;
                margin: 0px 0px 0px 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {ThemeConfig.TEXT_SECONDARY}50;
                min-height: 20px;
                border-radius: 5px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Global Dark Palette
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(ThemeConfig.BG_DARKER))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(ThemeConfig.TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Base, QColor(ThemeConfig.BG_DARK))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(ThemeConfig.BG_LIGHT))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(ThemeConfig.BG_LIGHT))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(ThemeConfig.TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Text, QColor(ThemeConfig.TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Button, QColor(ThemeConfig.BG_LIGHT))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(ThemeConfig.TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
    palette.setColor(QPalette.ColorRole.Link, QColor(ThemeConfig.ACCENT))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(ThemeConfig.ACCENT))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(ThemeConfig.BG_DARKER))
    
    app.setPalette(palette)
    
    # Set default font
    font = app.font()
    font.setFamily(ThemeConfig.FONT_FAMILY)
    font.setPointSize(ThemeConfig.FONT_SIZE_MAIN)
    app.setFont(font)
    
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--x", type=int, help="Window X position")
    parser.add_argument("--y", type=int, help="Window Y position")
    parser.add_argument("--width", type=int, help="Window width")
    parser.add_argument("--height", type=int, help="Window height")
    parser.add_argument("--always-on-top", action="store_true", help="Keep window always on top")
    parser.add_argument("--frameless", action="store_true", help="Frameless window mode")
    parser.add_argument("--title", type=str, help="Window title (e.g. Folder - Note)")
    parser.add_argument("--file", type=str, help="Auto-open specific whiteboard file")
    args, unknown = parser.parse_known_args()

    
    window = ScrbleInkPro()
    
    if args.title:
        window.setWindowTitle(args.title)
    
    # Apply geometry if provided
    if args.x is not None and args.y is not None:
        window.move(args.x, args.y)
    
    if args.width is not None and args.height is not None:
        window.resize(args.width, args.height)
        
    # Apply Window Flags
    flags = window.windowFlags()
    if args.always_on_top:
        flags |= Qt.WindowType.WindowStaysOnTopHint
    if args.frameless:
        flags |= Qt.WindowType.FramelessWindowHint
    
    window.setWindowFlags(flags)
    
    # Auto-Load File Logic
    if args.file:
        import os
        window.active_file_path = args.file # Store for Ctrl+S
        
        if os.path.exists(args.file):
            try:
                # Check if it's an image file (Edit Mode)
                if args.file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                    # Create new page with this image
                    # window._add_page() # _add_page might be automatically called or we need one.
                    # Verify if pages exist, if not add one.
                    if not window.pages:
                        window._add_page()
                    
                    # Use existing add_image logic which adds to the *current* page's list
                    # But we want it as a background or just an image?
                    # User said "Edit... open exact file". 
                    # Ideally, we load it into the canvas.
                    # The `add_image` method appends to `self.images`.
                    window.canvas.add_image(args.file)
                    
                    # Improve TOC: Set page name to Title if available
                    if window.pages:
                        if args.title:
                            window.pages[0].name = args.title
                        else:
                             # Use filename as fallback
                             import os
                             window.pages[0].name = os.path.basename(args.file)
                    
                    # Register in page data
                    # We need a robust way to persist this if we save as JSON
                    # For now, just allow editing on top
                    
                    # Set export override?
                    # We want Ctrl+S to overwrite the image
                    # But standard Save is for JSON.
                    # We can hack `_save_file` or use a flag.
                    window.image_edit_mode = True
                    window.image_edit_path = args.file
                else:
                    # Load existing JSON
                    window._load_file_path(args.file) # We need to refactor _open_file to separate load logic
                    
                    # Check last page for content
                    if window.pages:
                        last_page = window.pages[-1]
                        if last_page.strokes or last_page.images or last_page.shapes:
                            window._add_page()
                        
            except Exception as e:
                print(f"Error loading file: {e}")
        else:
            # New file will be created on save
            pass
            
    window.show()


    
    sys.exit(app.exec())
    
if __name__ == "__main__":
    main()