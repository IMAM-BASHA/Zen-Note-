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
        
        # Create Toolbars
        self._create_header_toolbar()    # TOP: Title & Nav
        self._create_tool_toolbar()      # Left
        self._create_main_toolbar()      # Right
        self._create_pen_toolbar()       # Top
        self._create_shape_toolbar()     # Top
        self._create_settings_toolbar()  # Top
        self._create_action_toolbar()    # Top (New)
        
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
            settings = QSettings("WhiteboardApp", "ToolbarLayout_v2")
            settings.setValue("geometry", self.saveGeometry())
            settings.setValue("windowState", self.saveState())
        except Exception as e:
            print(f"Error saving toolbar state: {e}")
    
    def restore_toolbar_state(self):
        """Restore toolbar positions and layout"""
        try:
            settings = QSettings("WhiteboardApp", "ToolbarLayout_v2")
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
        
        # Responsive Toolbar Layout for Actions
        if hasattr(self, 'action_toolbar'):
             # Check if we should force a new line
             should_break = self.width() < 1100
             
             # Strategy: maintain a state
             if not hasattr(self, '_action_toolbar_broken'):
                 self._action_toolbar_broken = False
                 
             if should_break and not self._action_toolbar_broken:
                 self.insertToolBarBreak(self.action_toolbar)
                 self._action_toolbar_broken = True
             elif not should_break and self._action_toolbar_broken:
                 # To "remove" a break, we sadly have to remove the toolbar and re-add it 
                 self.removeToolBar(self.action_toolbar)
                 self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.action_toolbar)
                 self._action_toolbar_broken = False
        
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

    def _create_header_toolbar(self):
        """Create Top Header with Title and Navigation"""
        toolbar = QToolBar("Header")
        toolbar.setObjectName("HeaderToolbar")
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)

        # Title
        self.lbl_title = QLabel(" 📁 Loading... ")
        self.lbl_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #4da6ff;")
        toolbar.addWidget(self.lbl_title)
        
        # Spacer
        dummy = QWidget()
        dummy.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        dummy.setStyleSheet("background: transparent;") # Fix: Ensure it's invisible
        toolbar.addWidget(dummy)
        
        # Prev
        prev_action = QAction("◀", self)
        prev_action.setToolTip("Previous Page")
        prev_action.triggered.connect(self._prev_page)
        toolbar.addAction(prev_action)
        
        # Page Info
        self.lbl_page_info = QLabel(" Page 1 / 1 ")
        self.lbl_page_info.setStyleSheet("font-weight: bold;")
        toolbar.addWidget(self.lbl_page_info)
        
        # Next
        next_action = QAction("▶", self)
        next_action.setToolTip("Next Page")
        next_action.triggered.connect(self._next_page)
        toolbar.addAction(next_action)
        
        toolbar.addSeparator()
        
        # Delete Page
        del_page_action = QAction("📄✖", self) # Page with X
        del_page_action.setToolTip("Delete Current Page")
        del_page_action.triggered.connect(self._delete_page)
        toolbar.addAction(del_page_action)
        
        # Insert to Note & Image moved to separate Action Toolbar for movability

    def _create_action_toolbar(self):
        """Create actions toolbar (Insert to Note, Image)"""
        toolbar = QToolBar("Actions")
        toolbar.setObjectName("ActionsToolbar_Embedded")
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
        save_action.triggered.connect(self._quick_to_editor)
        toolbar.addAction(save_action)
        
        toolbar.addSeparator()
        
        # Image Action
        img_action = QAction("📷 Image", self)
        img_action.setToolTip("Add Image - Import an image to the canvas")
        img_action.triggered.connect(self._add_image)
        toolbar.addAction(img_action)

    def _create_main_toolbar(self):
        """Create main toolbar with file operations"""
        toolbar = QToolBar("Main")
        toolbar.setObjectName("MainToolbar_Embedded") 
        toolbar.setMovable(True)
        toolbar.setFloatable(True)
        toolbar.setAllowedAreas(Qt.ToolBarArea.AllToolBarAreas)
        toolbar.setIconSize(QSize(20, 20))
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        # PLACEMENT: Right (Vertical) as requested
        self.addToolBar(Qt.ToolBarArea.RightToolBarArea, toolbar)
        
        # Close (Hide in embedded mode)
        close_action = QAction("❌", self)
        close_action.setToolTip("Close Whiteboard")
        close_action.triggered.connect(self.closed.emit) # Emit signal instead of just hiding
        toolbar.addAction(close_action)
        
        toolbar.addSeparator()
        
        # PDF
        export_pdf_action = QAction("📄 PDF", self)
        export_pdf_action.setToolTip("Export as PDF (All Pages)")
        export_pdf_action.triggered.connect(self._export_pdf_toc)
        toolbar.addAction(export_pdf_action)
        
        toolbar.addSeparator()
        
        # New page
        new_action = QAction("➕📄", self)
        new_action.setToolTip("New Page")
        new_action.triggered.connect(self._add_page)
        toolbar.addAction(new_action)
        
        # Save (Manual trigger for auto-save logic basically)
        save_action = QAction("💾", self)
        save_action.setToolTip("Save File (Ctrl+S)")
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(lambda: self.contentChanged.emit())
        toolbar.addAction(save_action)
        
        # Image Export
        export_action = QAction("📤", self)
        export_action.setToolTip("Export as Image")
        export_action.triggered.connect(self._export_image)
        toolbar.addAction(export_action)



        toolbar.addSeparator()
        
        # Undo/Redo (Hidden Shortcuts)
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

        
        toolbar.addSeparator()
        
        # Clear
        clear_action = QAction("🗑", self)
        clear_action.setToolTip("Clear Canvas")
        clear_action.triggered.connect(self._clear_canvas)
        toolbar.addAction(clear_action)

    def _create_tool_toolbar(self):
        """Create toolbar for drawing tools"""
        toolbar = QToolBar("Tools")
        toolbar.setObjectName("ToolsToolbar_Embedded")
        toolbar.setMovable(True)
        toolbar.setFloatable(True)
        toolbar.setAllowedAreas(Qt.ToolBarArea.AllToolBarAreas)
        # PLACEMENT: Left (Vertical)
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, toolbar)
        
        # Select
        select_action = QAction("👆", self)
        select_action.setToolTip("Select")
        select_action.setCheckable(True)
        select_action.setData(ToolType.SELECT)
        select_action.setActionGroup(self.tool_group)
        toolbar.addAction(select_action)
        

        
        toolbar.addSeparator()
        
        # Pen Tools
        pen_action = QAction("🖊", self)
        pen_action.setToolTip("Pen")
        pen_action.setCheckable(True)
        pen_action.setChecked(True)
        pen_action.setData(ToolType.PEN)
        pen_action.setActionGroup(self.tool_group)
        toolbar.addAction(pen_action)
        self.pen_action = pen_action # Ref for defaults
        
        ballpoint_action = QAction("🖊", self)
        ballpoint_action.setToolTip("Ballpoint")
        ballpoint_action.setCheckable(True)
        ballpoint_action.setData(ToolType.BALLPOINT)
        ballpoint_action.setActionGroup(self.tool_group)
        toolbar.addAction(ballpoint_action)
        
        pencil_action = QAction("✏", self)
        pencil_action.setToolTip("Pencil")
        pencil_action.setCheckable(True)
        pencil_action.setData(ToolType.PENCIL)
        pencil_action.setActionGroup(self.tool_group)
        toolbar.addAction(pencil_action)
        
        marker_action = QAction("🖍", self)
        marker_action.setToolTip("Marker")
        marker_action.setCheckable(True)
        marker_action.setData(ToolType.MARKER)
        marker_action.setActionGroup(self.tool_group)
        toolbar.addAction(marker_action)
        
        highlighter_action = QAction("🖌️", self)
        highlighter_action.setToolTip("Highlighter")
        highlighter_action.setCheckable(True)
        highlighter_action.setData(ToolType.HIGHLIGHTER)
        highlighter_action.setActionGroup(self.tool_group)
        toolbar.addAction(highlighter_action)
        
        toolbar.addSeparator()
        
        # Erasers
        eraser_action = QAction("🧽", self)
        eraser_action.setToolTip("Eraser")
        eraser_action.setCheckable(True)
        eraser_action.setData(ToolType.ERASER)
        eraser_action.setActionGroup(self.tool_group)
        toolbar.addAction(eraser_action)
        
        stroke_eraser_action = QAction("✂", self)
        stroke_eraser_action.setToolTip("Stroke Eraser")
        stroke_eraser_action.setCheckable(True)
        stroke_eraser_action.setData(ToolType.STROKE_ERASER)
        stroke_eraser_action.setActionGroup(self.tool_group)
        toolbar.addAction(stroke_eraser_action)

    def _create_pen_toolbar(self):
        """Create pen settings toolbar"""
        toolbar = QToolBar("Pen Settings")
        toolbar.setObjectName("PenSettingsToolbar_Embedded")
        toolbar.setMovable(True)
        toolbar.setFloatable(True)
        # PLACEMENT: Top (Horizontal)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)
        
        # Width
        self.lbl_width = QLabel(" Width: ")
        toolbar.addWidget(self.lbl_width)
        width_slider = QSlider(Qt.Orientation.Horizontal)
        width_slider.setMinimum(1)
        width_slider.setMaximum(50)
        width_slider.setValue(3)
        width_slider.setMaximumWidth(150)
        width_slider.valueChanged.connect(self._on_width_changed)
        toolbar.addWidget(width_slider)
        self.width_slider = width_slider
        
        self.width_label = QLabel("3px")
        self.width_label.setMinimumWidth(40)
        toolbar.addWidget(self.width_label)
        
        toolbar.addSeparator()
        
        # Smooth
        self.lbl_smooth = QLabel(" Smooth: ")
        toolbar.addWidget(self.lbl_smooth)
        smooth_slider = QSlider(Qt.Orientation.Horizontal)
        smooth_slider.setMinimum(0)
        smooth_slider.setMaximum(5)
        smooth_slider.setValue(2)
        smooth_slider.setMaximumWidth(100)
        smooth_slider.valueChanged.connect(lambda v: setattr(self.canvas, 'smoothing_level', v))
        toolbar.addWidget(smooth_slider)
        
        toolbar.addSeparator()
        
        # Colors
        self.lbl_colors = QLabel(" Colors: ")
        toolbar.addWidget(self.lbl_colors)
        for color in self.color_palette[:8]:
            btn = QPushButton()
            btn.setFixedSize(20, 20)
            btn.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #555; border-radius: 10px;")
            btn.clicked.connect(lambda checked, c=color: self.canvas.set_color(c))
            toolbar.addWidget(btn)
            
        custom_color_btn = QPushButton("⊕")
        custom_color_btn.setFixedSize(20, 20)
        custom_color_btn.clicked.connect(self._pick_custom_color)
        toolbar.addWidget(custom_color_btn)

    def _create_shape_toolbar(self):
        """Create shapes toolbar"""
        toolbar = QToolBar("Shapes")
        toolbar.setObjectName("ShapesToolbar_Embedded")
        toolbar.setMovable(True)
        toolbar.setFloatable(True)
        # PLACEMENT: Top (Horizontal)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)
        
        # Shapes
        shapes = [
            ("─", ToolType.LINE, "Line"),
            ("□", ToolType.RECTANGLE, "Rectangle"),
            ("○", ToolType.CIRCLE, "Circle"),
            ("➔", ToolType.ARROW, "Arrow"),
            ("↔", ToolType.DOUBLE_ARROW, "Double Arrow")
        ]
        
        for icon, tool, tooltip in shapes:
            action = QAction(icon, self)
            action.setToolTip(tooltip)
            action.setCheckable(True)
            action.setData(tool)
            action.setActionGroup(self.tool_group)
            toolbar.addAction(action)

    def _create_settings_toolbar(self):
        """Create settings toolbar"""
        toolbar = QToolBar("Settings")
        toolbar.setObjectName("SettingsToolbar_Embedded")
        toolbar.setMovable(True)
        toolbar.setFloatable(True)
        # PLACEMENT: Top (Horizontal)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)
        
        # Background
        self.lbl_bg = QLabel(" Background: ")
        toolbar.addWidget(self.lbl_bg)
        bg_combo = QComboBox()
        bg_combo.addItems(["Dots", "Grid", "Lines", "Lines + Margin", "Graph", "Plain"])
        bg_combo.currentIndexChanged.connect(self._change_background)
        toolbar.addWidget(bg_combo)
        
        bg_color_btn = QPushButton("BG Color")
        bg_color_btn.clicked.connect(self._pick_background_color)
        toolbar.addWidget(bg_color_btn)
        
        toolbar.addSeparator()
        
        toolbar.addSeparator()

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
