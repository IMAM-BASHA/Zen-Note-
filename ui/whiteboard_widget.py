"""
Embeddable Whiteboard Widget
Refactored to be a full QMainWindow for proper toolbar support (Floatable/Movable)
Integrates fully with scrble_ink1 logic.
"""

import sys
import json
import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QToolBar, 
                              QColorDialog, QPushButton, QLabel, QSlider, 
                              QFileDialog, QMessageBox, QComboBox,
                              QCheckBox, QFrame, QSizePolicy)
from PyQt6.QtCore import Qt, QPointF, QSize, pyqtSignal, QSettings, QRectF, QSizeF
from PyQt6.QtGui import (QPainter, QPen, QColor, QAction, QActionGroup,
                         QIcon, QCursor, QPixmap, QImage)
import ui.styles as styles

# Import all necessary components from scrble_ink1
import importlib.util
spec = importlib.util.spec_from_file_location("scrble_ink1", 
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "scrble_ink1.py"))
scrble_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scrble_module)

# Import all required classes
ThemeConfig = scrble_module.ThemeConfig
ToolType = scrble_module.ToolType
BackgroundType = scrble_module.BackgroundType
Stroke = scrble_module.Stroke
ShapeObject = scrble_module.ShapeObject
ImageObject = scrble_module.ImageObject
Page = scrble_module.Page
InkCanvas = scrble_module.InkCanvas
ModernMessageBox = scrble_module.ModernMessageBox


class WhiteboardWidget(QMainWindow):
    """
    Embeddable whiteboard widget for note application.
    Inherits QMainWindow to support QToolBars natively.
    """
    
    insert_requested = pyqtSignal(str, dict) # Path to image, metadata
    contentChanged = pyqtSignal()  # Emitted when content changes (for auto-save)
    closed = pyqtSignal()          # Emitted when close button is clicked
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # KEY: Allow being embedded as a widget despite being QMainWindow
        self.setWindowFlags(Qt.WindowType.Widget)
        
        # Page management
        self.pages = [Page(name="Page 1")]
        self.current_page_index = 0
        self.active_file_path = None
        self.folder_name = "Unsaved"
        
        # Color Palette (Copied from ScrbleInkPro)
        self.color_palette = [
            QColor("#000000"), QColor("#FFFFFF"),
            QColor("#FF0000"), QColor("#00FF00"),
            QColor("#0000FF"), QColor("#FFFF00"),
            QColor("#FF00FF"), QColor("#00FFFF"),
            QColor("#800000"), QColor("#008000"),
            QColor("#000080"), QColor("#808000"),
            QColor("#800080"), QColor("#008080"),
            QColor("#C0C0C0"), QColor("#808080")
        ]
        self.theme_mode = "light"
        
        # Setup UI
        self.init_ui()
        
    def init_ui(self):
        """Initialize UI components"""
        # Central Canvas
        self.canvas = InkCanvas(self)
        self.canvas.stroke_added.connect(self.contentChanged.emit)
        self.setCentralWidget(self.canvas)
        
        # Tool Action Group
        self.tool_group = QActionGroup(self)
        self.tool_group.setExclusive(True)
        self.tool_group.triggered.connect(self._on_tool_changed)
        
        # Create Unified Toolbars
        self._create_toolbars()
        
        # Load first page
        self.canvas.load_page_data(self.pages[self.current_page_index])
        
        # Apply Theme
        self._apply_professional_theme()
        
        # Restore toolbar positions
        self.restore_toolbar_state()
        
        # Sync UI controls with loaded canvas settings
        self.sync_ui_with_canvas_settings()
        
        # Connect toolbar movement to auto-save
        for toolbar in self.findChildren(QToolBar):
            toolbar.topLevelChanged.connect(self.save_toolbar_state)
            
    def set_theme_mode(self, mode):
        self.theme_mode = mode
        c = styles.ZEN_THEME.get(mode, styles.ZEN_THEME["light"])
        
        # Update Title Color
        if hasattr(self, 'lbl_title'):
             color = c['primary'] if mode == 'light' else '#60a5fa' # Blue-ish in dark
             self.lbl_title.setStyleSheet(f"font-weight: bold; font-size: 14px; color: {color};")
             
        # Update general window bg if needed (usually handled by global stylesheet)
        # But we can force it for embedded widget if needed
        pass
    
    def sync_ui_with_canvas_settings(self):
        """Sync UI controls (sliders, combo boxes) with loaded canvas settings"""
        # Note: width_slider and other controls are created in _create_pen_toolbar
        # This method should be called after all toolbars are created
        pass  # UI controls will be synced in their creation methods
        
    def save_toolbar_state(self):
        """Save toolbar positions and layout"""
        try:
            settings = QSettings("WhiteboardApp", "ToolbarLayout_v4")
            settings.setValue("geometry", self.saveGeometry())
            settings.setValue("windowState", self.saveState())
        except Exception as e:
            print(f"Error saving toolbar state: {e}")
    
    def restore_toolbar_state(self):
        """Restore toolbar positions and layout"""
        try:
            settings = QSettings("WhiteboardApp", "ToolbarLayout_v4")
            geometry = settings.value("geometry")
            state = settings.value("windowState")
            
            if geometry:
                self.restoreGeometry(geometry)
            if state:
                self.restoreState(state)
        except Exception as e:
            print(f"Error restoring toolbar state: {e}")
    
    def closeEvent(self, event):
        """Save state when closing"""
        self.save_toolbar_state()
        super().closeEvent(event)
    
    def hideEvent(self, event):
        """Save state when hiding (hiding whiteboard widget)"""
        self.save_toolbar_state()
        super().hideEvent(event)

    def resizeEvent(self, event):
        """Handle responsive layout"""
        super().resizeEvent(event)
        
    def set_info(self, folder_name, note_name=None):
        """Update context info"""
        self.folder_name = folder_name
        self.note_name = note_name
        self._update_page_display()

    def _update_page_display(self):
        """Update header and controls"""
        if hasattr(self, 'lbl_title'):
            if hasattr(self, 'note_name') and self.note_name:
                self.lbl_title.setText(f" 📁 {self.folder_name}  ➜  📝 {self.note_name} ")
            else:
                self.lbl_title.setText(f" 📁 {self.folder_name}  ")
        
        if hasattr(self, 'lbl_page_info'):
            self.lbl_page_info.setText(f" Page {self.current_page_index + 1} / {len(self.pages)} ")

    def _create_svg_icon(self, path_d, color="#cccccc", size=24):
        """Helper to generate clean SVG icons dynamically"""
        from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
        from PyQt6.QtCore import Qt, QByteArray
        from PyQt6.QtSvg import QSvgRenderer
        
        # We enforce a strictly colored icon path
        svg = f'''<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg"><path d="{path_d}"/></svg>'''
        
        renderer = QSvgRenderer(QByteArray(svg.encode('utf-8')))
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        renderer.render(painter)
        painter.end()
        
        return QIcon(pixmap)

    def _create_toolbars(self):
        """Create clean, consolidated, locked toolbars"""
        # 1. TOP TOOLBAR (Navigation & Actions)
        top_bar = QToolBar("Header")
        top_bar.setObjectName("TopToolbar_Embedded")
        top_bar.setMovable(False)
        top_bar.setFloatable(False)
        top_bar.setIconSize(QSize(18, 18))
        top_bar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        # FORCE: Never use extension overflow arrow; take up multiple rows if needed
        top_bar.setStyleSheet("QToolBar { border: none; } QToolBar::extension-button { width: 0px; }")
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, top_bar)

        # Title
        self.lbl_title = QLabel(" 📁 Loading... ")
        self.lbl_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #4da6ff; padding: 0 10px;")
        top_bar.addWidget(self.lbl_title)
        
        # Spacer
        dummy = QWidget()
        dummy.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        dummy.setStyleSheet("background: transparent;")
        top_bar.addWidget(dummy)

        # Navigation
        prev_action = QAction("◀", self)
        prev_action.setToolTip("Previous Page")
        prev_action.triggered.connect(self._prev_page)
        top_bar.addAction(prev_action)
        
        self.lbl_page_info = QLabel(" Page 1 / 1 ")
        self.lbl_page_info.setStyleSheet("font-weight: bold; padding: 0 10px;")
        top_bar.addWidget(self.lbl_page_info)
        
        next_action = QAction("▶", self)
        next_action.setToolTip("Next Page")
        next_action.triggered.connect(self._next_page)
        top_bar.addAction(next_action)
        
        # Add / Delete Pages
        add_page_action = QAction("➕", self)
        add_page_action.setToolTip("New Page")
        add_page_action.triggered.connect(self._add_page)
        top_bar.addAction(add_page_action)

        del_page_action = QAction("✖", self)
        del_page_action.setToolTip("Delete Current Page")
        del_page_action.triggered.connect(self._delete_page)
        top_bar.addAction(del_page_action)
        
        top_bar.addSeparator()

        # Background
        self.lbl_bg = QLabel(" Background: ")
        top_bar.addWidget(self.lbl_bg)
        bg_combo = QComboBox()
        bg_combo.addItems(["Dots", "Grid", "Lines", "Lines + Margin", "Graph", "Plain"])
        bg_combo.currentIndexChanged.connect(self._change_background)
        top_bar.addWidget(bg_combo)
        
        bg_color_btn = QPushButton("BG Color")
        bg_color_btn.clicked.connect(self._pick_background_color)
        top_bar.addWidget(bg_color_btn)
        
        # 1b. ACTION TOOLBAR (File Operations, Insert, Export)
        # Added below top_bar to prevent horizontal overflow
        action_bar = QToolBar("Actions")
        action_bar.setObjectName("ActionBar_Embedded")
        action_bar.setMovable(False)
        action_bar.setFloatable(False)
        action_bar.setIconSize(QSize(18, 18))
        action_bar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        action_bar.setStyleSheet("QToolBar { border: none; } QToolBar::extension-button { width: 0px; }")
        self.addToolBarBreak(Qt.ToolBarArea.TopToolBarArea)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, action_bar)

        # Document Actions
        img_action = QAction("🖼️ Image", self)
        img_action.setToolTip("Add Image")
        img_action.triggered.connect(self._add_image)
        action_bar.addAction(img_action)

        export_action = QAction("📤 Export", self)
        export_action.setToolTip("Export as Image")
        export_action.triggered.connect(self._export_image)
        action_bar.addAction(export_action)

        export_pdf_action = QAction("📄 PDF", self)
        export_pdf_action.setToolTip("Export as PDF")
        export_pdf_action.triggered.connect(self._export_pdf_toc)
        action_bar.addAction(export_pdf_action)
        
        save_action_main = QAction("💾 Save", self)
        save_action_main.setToolTip("Save File (Ctrl+S)")
        save_action_main.setShortcut("Ctrl+S")
        save_action_main.triggered.connect(lambda: self.contentChanged.emit())
        action_bar.addAction(save_action_main)

        clear_action = QAction("🗑️ Clear", self)
        clear_action.setToolTip("Clear Canvas")
        clear_action.triggered.connect(self._clear_canvas)
        action_bar.addAction(clear_action)

        action_bar.addSeparator()

        # Insert to Note
        save_action = QAction("✔️ Insert to Note", self)
        save_action.setToolTip("Insert to Note")
        save_action.triggered.connect(self._quick_to_editor)
        action_bar.addAction(save_action)

        # Close
        close_action = QAction("❌", self)
        close_action.setToolTip("Close Whiteboard")
        close_action.triggered.connect(self.closed.emit)
        action_bar.addAction(close_action)

        # Undo/Redo Hidden Action (Just added to window, not toolbar)
        undo_action = QAction("Undo", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.setShortcutContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        undo_action.triggered.connect(self.canvas.undo)
        self.addAction(undo_action)
        
        redo_action = QAction("Redo", self)
        redo_action.setShortcut("Ctrl+Y")
        redo_action.setShortcutContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        redo_action.triggered.connect(self.canvas.redo)
        self.addAction(redo_action)


        # 2. LEFT TOOLBAR (Tools & Shapes)
        left_bar = QToolBar("Tools")
        left_bar.setObjectName("LeftToolbar_Embedded")
        left_bar.setMovable(False)
        left_bar.setFloatable(False)
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, left_bar)

        icon_color = "#d4d4d8" # Light gray for dark theme compatibility

        # Tool Icons
        sel_icon = self._create_svg_icon("M3 3l7.07 16.97 2.51-7.39 7.39-2.51L3 3z", icon_color)
        pen_icon = self._create_svg_icon("M12 19l7-7 3 3-7 7-3-3z M18 13l-1.5-7.5L2 2l3.5 14.5L13 18l5-5z", icon_color)
        ballpoint_icon = self._create_svg_icon("M3 21l3.75-3.75 L16.5 7.5l-3-3L3.75 14.25 3 21z M13.5 4.5l6 6", icon_color)
        pencil_icon = self._create_svg_icon("M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z", icon_color)
        marker_icon = self._create_svg_icon("M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z M15 5l4 4", icon_color)
        highlighter_icon = self._create_svg_icon("M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z M14.5 6.5l3 3 M9 18l1.5 1.5 M15.5 11.5l1.5 1.5 M4 20l2-2", icon_color)
        eraser_icon = self._create_svg_icon("M20 20H7L3 16C2.5 15.5 2.5 14.5 3 14L13 4C13.5 3.5 14.5 3.5 15 4L20 9C20.5 9.5 20.5 10.5 20 11L11 20M15 4l5 5", icon_color)
        stroke_eraser_icon = self._create_svg_icon("M21 4H8l-7 8 7 8h13a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2z M18 9l-6 6 M12 9l6 6", icon_color)

        tools = [
            ("Select", sel_icon, ToolType.SELECT, "Select Tool"),
            ("Pen", pen_icon, ToolType.PEN, "Normal Pen"),
            ("Ballpoint", ballpoint_icon, ToolType.BALLPOINT, "Ballpoint Pen"),
            ("Pencil", pencil_icon, ToolType.PENCIL, "Pencil"),
            ("Marker", marker_icon, ToolType.MARKER, "Marker"),
            ("Highlight", highlighter_icon, ToolType.HIGHLIGHTER, "Highlighter"),
            ("Eraser", eraser_icon, ToolType.ERASER, "Free Eraser"),
            ("Stroke Eraser", stroke_eraser_icon, ToolType.STROKE_ERASER, "Stroke Eraser"),
        ]

        # Use an ActionGroup for exclusive selection
        self.tool_group = QActionGroup(self)
        self.tool_group.setExclusive(True)
        self.tool_group.triggered.connect(self._on_tool_changed)

        for name, icon, tool_type, tip in tools:
            action = QAction(icon, "", self)
            action.setToolTip(tip)
            action.setCheckable(True)
            action.setData(tool_type)
            action.setActionGroup(self.tool_group)
            if tool_type == ToolType.PEN:
                action.setChecked(True)
                self.pen_action = action
            left_bar.addAction(action)

        left_bar.addSeparator()

        line_icon = self._create_svg_icon("M3 21L21 3", icon_color)
        rect_icon = self._create_svg_icon("M3 3h18v18H3z", icon_color)
        circ_icon = self._create_svg_icon("M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18z", icon_color)
        arrow_icon = self._create_svg_icon("M5 12h14 M12 5l7 7-7 7", icon_color)
        darrow_icon = self._create_svg_icon("M5 12h14 M12 5l7 7-7 7 M12 5L5 12l7 7", icon_color)

        shapes = [
            ("Line", line_icon, ToolType.LINE, "Line"),
            ("Rect", rect_icon, ToolType.RECTANGLE, "Rectangle"),
            ("Circle", circ_icon, ToolType.CIRCLE, "Circle"),
            ("Arrow", arrow_icon, ToolType.ARROW, "Arrow"),
            ("D-Arrow", darrow_icon, ToolType.DOUBLE_ARROW, "Double Arrow")
        ]

        for name, icon, tool_type, tip in shapes:
            action = QAction(icon, "", self)
            action.setToolTip(tip)
            action.setCheckable(True)
            action.setData(tool_type)
            action.setActionGroup(self.tool_group)
            left_bar.addAction(action)


        # 3. SECONDARY TOP TOOLBAR (Pen Settings)
        # This keeps the settings cleanly organized just below the action_bar
        prop_bar = QToolBar("Properties")
        prop_bar.setObjectName("PropertiesToolbar_Embedded")
        prop_bar.setMovable(False)
        prop_bar.setFloatable(False)
        prop_bar.setStyleSheet("QToolBar { border: none; } QToolBar::extension-button { width: 0px; }")
        self.addToolBarBreak(Qt.ToolBarArea.TopToolBarArea)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, prop_bar)

        self.lbl_width = QLabel(" Width: ")
        prop_bar.addWidget(self.lbl_width)
        
        width_slider = QSlider(Qt.Orientation.Horizontal)
        width_slider.setMinimum(1)
        width_slider.setMaximum(50)
        width_slider.setValue(3)
        width_slider.setMaximumWidth(150)
        width_slider.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        width_slider.valueChanged.connect(self._on_width_changed)
        prop_bar.addWidget(width_slider)
        self.width_slider = width_slider
        
        self.width_label = QLabel("3px")
        self.width_label.setMinimumWidth(40)
        self.width_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        prop_bar.addWidget(self.width_label)
        
        prop_bar.addSeparator()
        
        self.lbl_smooth = QLabel(" Smooth: ")
        prop_bar.addWidget(self.lbl_smooth)
        
        smooth_slider = QSlider(Qt.Orientation.Horizontal)
        smooth_slider.setMinimum(0)
        smooth_slider.setMaximum(5)
        smooth_slider.setValue(2)
        smooth_slider.setMaximumWidth(100)
        smooth_slider.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        smooth_slider.valueChanged.connect(lambda v: setattr(self.canvas, 'smoothing_level', v))
        prop_bar.addWidget(smooth_slider)
        
        prop_bar.addSeparator()
        
        self.lbl_colors = QLabel(" Colors: ")
        prop_bar.addWidget(self.lbl_colors)
        
        for color in self.color_palette[:16]:
            btn = QPushButton()
            btn.setFixedSize(22, 22)
            btn.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #444; border-radius: 11px;")
            btn.clicked.connect(lambda checked, c=color: self.canvas.set_color(c))
            prop_bar.addWidget(btn)
            
        custom_color_btn = QPushButton("⊕")
        custom_color_btn.setFixedSize(22, 22)
        custom_color_btn.setStyleSheet("border: 1px solid #444; border-radius: 11px; font-weight: bold;")
        custom_color_btn.setToolTip("Custom Color")
        custom_color_btn.clicked.connect(self._pick_custom_color)
        prop_bar.addWidget(custom_color_btn)

    def _on_tool_changed(self, action):
        """Handle tool selection"""
        tool = action.data()
        self.canvas.set_tool(tool)
        
        # Update width slider for eraser
        self.width_slider.blockSignals(True)
        if tool == ToolType.ERASER:
            if hasattr(self.canvas, 'eraser_width'):
                self.width_slider.setValue(int(self.canvas.eraser_width))
                self.width_label.setText(f"{int(self.canvas.eraser_width)}px")
        elif tool in self.canvas.pen_styles:
            width = int(self.canvas.pen_styles[tool]['width'])
            self.width_slider.setValue(width)
            self.width_label.setText(f"{width}px")
        self.width_slider.blockSignals(False)
    
    def _on_width_changed(self, value):
        """Handle width slider change"""
        if self.canvas.current_tool == ToolType.ERASER:
            self.canvas.eraser_width = value
        else:
            self.canvas.set_pen_width(value)
        self.width_label.setText(f"{value}px")
        self.canvas.update()
        self.contentChanged.emit()
        
    def _change_background(self, index):
        bg_types = [BackgroundType.DOTS, BackgroundType.GRID, 
                   BackgroundType.LINES, BackgroundType.LINES_WITH_MARGIN, 
                   BackgroundType.GRAPH, BackgroundType.PLAIN]
        if 0 <= index < len(bg_types):
            self.canvas.set_background_type(bg_types[index])
            self.contentChanged.emit()
            
    def _pick_custom_color(self):
        color = QColorDialog.getColor(self.canvas.current_color, self, "Select Color")
        if color.isValid():
            self.canvas.set_color(color)
            
    def _pick_background_color(self):
        color = QColorDialog.getColor(self.canvas.background_color, self, "Select Background Color")
        if color.isValid():
            self.canvas.set_background_color(color)
            self.contentChanged.emit()
            
        
    def _add_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Add Image", "", 
                                                 "Images (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            self.canvas.add_image(file_path)
            self.contentChanged.emit()
            
    def _add_page(self):
        # Save current
        self.canvas.save_page_data(self.pages[self.current_page_index])
        
        # New page
        new_page_index = len(self.pages) + 1
        new_page = Page(name=f"Page {new_page_index}")
        
        # Auto-assign section if currently in a note
        if hasattr(self, 'current_section') and self.current_section:
            new_page.section = self.current_section
            
        self.pages.append(new_page)
        self.current_page_index = len(self.pages) - 1
        self.canvas.load_page_data(self.pages[self.current_page_index])
        self._update_page_display()
        self.contentChanged.emit()
        
    def _delete_page(self):
        """Delete current page"""
        if len(self.pages) <= 1:
            QMessageBox.information(self, "Cannot Delete", "You must have at least one page.")
            return

        confirm = QMessageBox.question(self, "Delete Page", 
                                     f"Are you sure you want to delete Page {self.current_page_index + 1}?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if confirm == QMessageBox.StandardButton.Yes:
            self.pages.pop(self.current_page_index)
            # Adjust index
            if self.current_page_index >= len(self.pages):
                self.current_page_index = len(self.pages) - 1
            
            self.canvas.load_page_data(self.pages[self.current_page_index])
            self._update_page_display()
            self.contentChanged.emit()

    def set_info(self, folder_name, note_name=None):
        """Update context info"""
        self.folder_name = folder_name
        self.note_name = note_name
        self.current_section = note_name if note_name else ""
        
        # If a note is selected and current page has NO section, adopt it
        # This allows "Book Mode": clicking a note claims the current untitled page
        if note_name and self.current_page_index < len(self.pages):
           if not self.pages[self.current_page_index].section:
               self.pages[self.current_page_index].section = note_name
               
        self._update_page_display()

    def _update_page_display(self):
        """Update header and controls"""
        if hasattr(self, 'lbl_title'):
            # Priority: Page Section -> Selected Note -> Just Folder
            current_page = self.pages[self.current_page_index]
            display_section = current_page.section if current_page.section else self.note_name
            
            if display_section:
                full_text = f" 📁 {self.folder_name}  ➜  📝 {display_section} "
            else:
                full_text = f" 📁 {self.folder_name}  "

            # Truncate text if too long (max 350px)
            from PyQt6.QtGui import QFontMetrics
            font_metrics = QFontMetrics(self.lbl_title.font())
            elided_text = font_metrics.elidedText(full_text, Qt.TextElideMode.ElideRight, 350)
            
            self.lbl_title.setText(elided_text)
            self.lbl_title.setToolTip(full_text) # Show full text on hover
        
        if hasattr(self, 'lbl_page_info'):
            # Show Page Name in UI if it's custom
            pg_name = self.pages[self.current_page_index].name
            if "Page" in pg_name and len(pg_name) < 10:
                 self.lbl_page_info.setText(f" {pg_name} / {len(self.pages)} ")
            else:
                 # Truncate if long note name
                 disp_name = (pg_name[:15] + '..') if len(pg_name) > 15 else pg_name
                 self.lbl_page_info.setText(f" {disp_name} ({self.current_page_index + 1}/{len(self.pages)}) ")

    def _quick_to_editor(self):
        """Capture current view and send to editor"""
        import tempfile
        try:
            # Create temp file
            fd, path = tempfile.mkstemp(suffix='.png')
            os.close(fd)
            
            # Grab and save
            pixmap = self.canvas.grab()
            pixmap.save(path)
            
            # Create proper metadata
            metadata = {
                'wb_file': self.active_file_path if hasattr(self, 'active_file_path') else None,
                'wb_page': self.current_page_index
            }
            
            # Emit signal
            self.insert_requested.emit(path, metadata)
            
            # Visual feedback
            # ModernMessageBox("Success", "Inserted to Note!", QMessageBox.StandardButton.Ok, self).exec()
        except Exception as e:
            print(f"Error quick saving: {e}")

    def _prev_page(self):
        if self.current_page_index > 0:
            self.canvas.save_page_data(self.pages[self.current_page_index])
            self.current_page_index -= 1
            self.canvas.load_page_data(self.pages[self.current_page_index])
            self._update_page_display()
            
    def _next_page(self):
        if self.current_page_index < len(self.pages) - 1:
            self.canvas.save_page_data(self.pages[self.current_page_index])
            self.current_page_index += 1
            self.canvas.load_page_data(self.pages[self.current_page_index])
            self._update_page_display()
            
    def go_to_page(self, index):
        """Public method to jump to specific page index"""
        if 0 <= index < len(self.pages):
            self.current_page_index = index
            self.canvas.load_page_data(self.pages[index])
            self._update_page_display()

    def _export_image(self):
        if not self.active_file_path: return
        folder = os.path.dirname(self.active_file_path)
        path, _ = QFileDialog.getSaveFileName(self, "Export Image", folder, "PNG (*.png);;JPEG (*.jpg)")
        if path:
            pixmap = self.canvas.grab()
            pixmap.save(path)
            
    def _export_pdf_toc(self):
        """Export whiteboard to PDF with detailed Table of Contents."""
        if not self.active_file_path: return
        folder = os.path.dirname(self.active_file_path)
        
        # Default filename
        default_name = f"{self.folder_name}_Whiteboard.pdf"
        filename, _ = QFileDialog.getSaveFileName(self, "Export Whiteboard to PDF", os.path.join(folder, default_name), "PDF (*.pdf)")
        
        if not filename: return
        
        try:
            from PyQt6.QtGui import QTextDocument, QPageSize, QFont
            from PyQt6.QtCore import QSizeF, QBuffer, QIODevice, QByteArray
            from PyQt6.QtPrintSupport import QPrinter
            from PyQt6.QtWidgets import QApplication
            import base64
            
            # 1. Generate HTML Content
            html_parts = []
            
            # Title
            html_parts.append(f"""
            <div style="text-align: center; margin-top: 50px;">
                <h1 style="font-size: 32pt; font-weight: bold; color: #000;">{self.folder_name}</h1>
                <p style="color: #666; font-size: 14pt;">Whiteboard Export</p>
            </div>
            <br/><hr/><br/>
            """)
            
            # TOC
            html_parts.append('<div id="toc"><h2 style="color: #000;">Table of Contents</h2></div><ul style="font-size: 14pt; line-height: 1.6;">')
            
            current_section = None
            for i, page in enumerate(self.pages):
                anchor = f"page_{i}"
                page_name = page.name if page.name else f"Page {i+1}"
                
                # Check for new section
                if page.section and page.section != current_section:
                    current_section = page.section
                    html_parts.append(f'<li style="list-style: none; margin-top: 15px; font-weight: bold; font-size: 16pt; color: #333;">📝 {current_section}</li>')
                
                # Indent pages under section
                indent = 'margin-left: 20px;' if current_section else ''
                html_parts.append(f'<li style="{indent}"><a href="#{anchor}" style="text-decoration: underline; color: #007ACC;">{page_name}</a></li>')
                
            html_parts.append("</ul><br/><hr/><br/><br/>")
            
            # 2a. Save CURRENT page state before switching so we don't lose pending edits
            self.canvas.save_page_data(self.pages[self.current_page_index])
            
            # Content
            for i, page in enumerate(self.pages):
                # Switch to page (Load ONLY, do NOT save current canvas into it!)
                # REMOVED clear_canvas() to prevent wiping shared list references! 
                self.canvas.load_page_data(self.pages[i])
                QApplication.processEvents() 
                print(f"DEBUG: Export Page {i}, Images: {len(self.canvas.images)}")
                                
                # Render High-Res Image
                pixmap = self._render_canvas_to_pixmap()
                
                # Convert to base64
                ba = QByteArray()
                buf = QBuffer(ba)
                buf.open(QIODevice.OpenModeFlag.WriteOnly)
                pixmap.save(buf, "PNG")
                b64_data = ba.toBase64().data().decode()
                
                anchor = f"page_{i}"
                page_name = page.name if page.name else f"Page {i+1}"
                
                # Calculate fit dimensions for A4 (approx 700x950 logical pixels safe area)
                # This manually implements 'object-fit: contain' which QTextDocument lacks
                SAFE_W = 700
                SAFE_H = 800 # Reduced to ensure Title + Image fits on one page
                
                img_w = pixmap.width()
                img_h = pixmap.height()
                aspect = img_w / img_h if img_h > 0 else 1
                
                # Scale to fit SAFE box
                if img_w > SAFE_W or img_h > SAFE_H:
                    ratio_w = SAFE_W / img_w
                    ratio_h = SAFE_H / img_h
                    ratio = min(ratio_w, ratio_h)
                    final_w = int(img_w * ratio)
                    final_h = int(img_h * ratio)
                else:
                    final_w = img_w
                    final_h = img_h

                html_parts.append(f"""
                <div id="{anchor}" style="page-break-before: always; page-break-inside: avoid; width: 100%; display: block;">
                    <h2 style="color: #333; border-bottom: 2px solid #ccc; margin-bottom: 20px;">{i+1}. {page_name}</h2>
                    
                    <table width="100%" border="0" cellpadding="0" cellspacing="0">
                        <tr>
                            <td align="center" valign="middle">
                                <img src="data:image/png;base64,{b64_data}" width="{final_w}" height="{final_h}" style="border: 1px solid #ddd;"/>
                            </td>
                        </tr>
                    </table>
                    
                    <div style="text-align: right; margin-top: 10px;">
                        <a href="#toc" style="text-decoration: none; color: #007ACC; font-size: 10pt;">↑ Back to Table of Contents</a>
                    </div>
                </div>
                """)
            
            # Restore current page
            self.canvas.load_page_data(self.pages[self.current_page_index])
            
            # 2. Print HTML to PDF
            html_content = "".join(html_parts)
            
            doc = QTextDocument()
            doc.setDefaultFont(QFont("Segoe UI", 10))
            doc.setHtml(html_content)
            
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(filename)
            printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
            
            doc.print(printer)
            
            QMessageBox.information(self, "Success", f"Whiteboard exported to:\n{filename}")
            
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export PDF:\n{e}")
            import traceback
            traceback.print_exc()

    def _render_canvas_to_pixmap(self):
        """Render the entire canvas content to a high-res pixmap with auto-scaling."""
        # 1. Calculate Bounds
        bounds = QRectF()
        
        # Strokes
        for s in self.canvas.strokes:
            if hasattr(s, 'path'):
                r = s.path.boundingRect()
                # Strokes have width, so we must inflate bounds by half width to capturing edges
                w = s.width / 2 + 5 # Add margin
                r.adjust(-w, -w, w, w)
                bounds = bounds.united(r)
                
        # Shapes
        for s in self.canvas.shapes:
            r = QRectF(s.start, s.end).normalized()
            adj = s.width / 2 + 5
            r.adjust(-adj, -adj, adj, adj)
            bounds = bounds.united(r)
            
        # Images
        for img in self.canvas.images:
            r = QRectF(img.position, QSizeF(img.size))
            bounds = bounds.united(r)
            
        if bounds.isEmpty():
            bounds = QRectF(0, 0, 800, 600)
            
        # Add Padding
        padding = 50
        bounds.adjust(-padding, -padding, padding, padding)
        
        # 2. Determine Scale for High-Res Output
        # We want the content to have a fixed "High Quality" width regardless of how small drawing is
        TARGET_WIDTH = 2000 
        scale_factor = TARGET_WIDTH / bounds.width()
        
        # Limit extreme scaling for tiny dots to avoid 1GB images
        # scale_factor = min(scale_factor, 5.0) # REMOVED: Vector strokes can scale infinitely
        # Also limit downscaling
        scale_factor = max(scale_factor, 1.0)
        
        w = int(bounds.width() * scale_factor)
        h = int(bounds.height() * scale_factor)
        
        # Cap max dimensions for safety
        MAX_DIM = 4000
        if w > MAX_DIM or h > MAX_DIM:
            ratio = min(MAX_DIM/w, MAX_DIM/h)
            scale_factor *= ratio
            w = int(bounds.width() * scale_factor)
            h = int(bounds.height() * scale_factor)

        image = QImage(w, h, QImage.Format.Format_ARGB32)
        
        # 3. Fill with Actual Background Color (WYSIWYG)
        # Check current page background color
        try:
            bg_color = self.pages[self.current_page_index].background_color
            image.fill(bg_color)
        except:
            image.fill(Qt.GlobalColor.white)
        
        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 4. Apply Transforms: Scale -> Translate
        # Note: Order matters. We translate logical coords to 0,0 then scale up.
        painter.scale(scale_factor, scale_factor)
        painter.translate(-bounds.topLeft())
        
        # Draw Content
        # Images
        for img_obj in self.canvas.images:
            painter.drawImage(QRectF(img_obj.position, QSizeF(img_obj.size)), img_obj.image)
            
        # Shapes
        for shape in self.canvas.shapes:
            self.canvas._draw_shape(painter, shape)
            
        # Strokes
        for stroke in self.canvas.strokes:
            self.canvas._draw_stroke(painter, stroke)
            
        painter.end()
        return QPixmap.fromImage(image)

    def _clear_canvas(self):
        self.canvas.clear_canvas()
        self.contentChanged.emit()
            
    def resizeEvent(self, event):
        """Handle responsive layout - hide labels if too small"""
        is_compact = self.width() < 800
        if hasattr(self, 'lbl_width'): self.lbl_width.setVisible(not is_compact)
        if hasattr(self, 'lbl_smooth'): self.lbl_smooth.setVisible(not is_compact)
        if hasattr(self, 'lbl_colors'): self.lbl_colors.setVisible(not is_compact)
        if hasattr(self, 'lbl_bg'): self.lbl_bg.setVisible(not is_compact)
        super().resizeEvent(event)

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
            QToolButton {{
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: {ThemeConfig.RADIUS}px;
                padding: 2px;
                color: {ThemeConfig.TEXT_SECONDARY};
                font-size: 14px;
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
                background-color: transparent;
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
                background-color: transparent;
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
        """)

    def load_file(self, filepath):
        """Load whiteboard from JSON file"""
        self.active_file_path = filepath
        if not os.path.exists(filepath):
            self.pages = [Page(name="Page 1")]
            self.current_page_index = 0
            self.canvas.load_page_data(self.pages[0])
            return
            
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            self.pages = [Page.from_dict(p) for p in data.get('pages', [])]
            if not self.pages: self.pages = [Page(name="Page 1")]
            self.current_page_index = data.get('current_page', 0)
            self.canvas.load_page_data(self.pages[self.current_page_index])
        except Exception as e:
            print(f"Error loading: {e}")
            self.pages = [Page(name="Page 1")]
            self.canvas.load_page_data(self.pages[0])
            
        self._update_page_display()

    def clear(self):
        """Reset the whiteboard to a single blank page."""
        self.pages = [Page(name="Page 1")]
        self.current_page_index = 0
        if hasattr(self, 'canvas'):
            self.canvas.load_page_data(self.pages[0])
        self.active_file_path = None
        self._update_page_display()

    def save_file(self, filepath):
        """Save whiteboard"""
        try:
            self.canvas.save_page_data(self.pages[self.current_page_index])
            data = {
                'version': '2.0',
                'pages': [page.to_dict() for page in self.pages],
                'current_page': self.current_page_index
            }
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            self.active_file_path = filepath
            return True
        except Exception as e:
            print(f"Error saving: {e}")
            return False
