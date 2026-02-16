from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QSpacerItem, QSizePolicy, QApplication,
    QToolButton, QComboBox, QSpinBox, QMenu, QDialog, QVBoxLayout, QListWidget, 
    QListWidgetItem, QDialogButtonBox, QCheckBox, QScrollArea, QFrame, QWidgetAction
)
from PyQt6.QtCore import Qt, QSize, QPoint, QSettings
from PyQt6.QtGui import QIcon, QAction, QCursor
from util.icon_factory import get_premium_icon
import ui.styles as styles

class CustomizeToolbarDialog(QDialog):
    """Dialog to toggle visibility of toolbar items."""
    def __init__(self, all_actions, hidden_ids, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Customize Toolbar")
        self.setFixedSize(300, 400)
        
        # Sanitize actions (remove dead ones to prevent crash)
        self.all_actions = []
        for item in all_actions:
            try:
                if isinstance(item, QWidget):
                    # Check liveness
                    _ = item.toolTip() 
                self.all_actions.append(item)
            except RuntimeError:
                continue
                
        self.hidden_ids = set(hidden_ids) # Working copy
        self.check_map = {} # id -> checkbox

        layout = QVBoxLayout(self)
        
        lbl = QLabel("Check items to show in the toolbar:")
        lbl.setWordWrap(True)
        layout.addWidget(lbl)
        
        # Scroll Area for list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        content = QWidget()
        self.list_layout = QVBoxLayout(content)
        self.list_layout.setSpacing(5)
        self.list_layout.setContentsMargins(10, 10, 10, 10)
        
        # Populate
        for item in self.all_actions:
            if item == "SEPARATOR":
                continue
                
            # Get ID and Name
            item_id = self._get_item_id(item)
            if not item_id: continue
            
            # Display Name
            display_name = item_id
            if isinstance(item, QAction) and item.text():
                 display_name = item.text()
            
            # Create Checkbox
            chk = QCheckBox(display_name) 
            chk.setChecked(item_id not in self.hidden_ids)
            chk.stateChanged.connect(lambda state, i=item_id: self._on_check_changed(state, i))
            
            self.list_layout.addWidget(chk)
            self.check_map[item_id] = chk
            
        self.list_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        # Buttons
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)
        
        # Apply Theme (Basic)
        self._apply_theme()

    def _get_item_id(self, item):
        """Helper to extract ID from item."""
        try:
            if isinstance(item, QWidget):
                return item.toolTip()
            elif isinstance(item, QAction):
                return item.toolTip() or item.text()
        except RuntimeError:
            return None
        return None

    def _on_check_changed(self, state, item_id):
        if state == Qt.CheckState.Checked.value:
            if item_id in self.hidden_ids:
                self.hidden_ids.remove(item_id)
        else:
            self.hidden_ids.add(item_id)

    def get_hidden_ids(self):
        return list(self.hidden_ids)

    def _apply_theme(self):
        mode = self.parent().property("theme_mode") if self.parent() else "light"
        c = styles.ZEN_THEME.get(mode, styles.ZEN_THEME["light"])
        
        self.setStyleSheet(f"""
            QDialog {{ background-color: {c['background']}; }}
            QLabel {{ color: {c['foreground']}; font-size: 14px; font-weight: 500; }}
            QScrollArea {{ border: 1px solid {c['border']}; border-radius: 8px; background: {c['card']}; }}
            QWidget#ScrollContent {{ background: {c['card']}; }}
            QCheckBox {{ color: {c['foreground']}; padding: 8px; font-size: 13px; }}
            QCheckBox::indicator {{ width: 18px; height: 18px; border-radius: 4px; border: 2px solid {c['border']}; }}
            QCheckBox::indicator:checked {{ background-color: {c['primary']}; border-color: {c['primary']}; }}
            QPushButton {{ 
                background: {c['secondary']}; color: {c['secondary_foreground']}; 
                border-radius: 8px; padding: 8px 16px; border: 1px solid {c['border']};
            }}
            QPushButton:hover {{ background: {c['accent']}; }}
        """)

class ToolbarActionWidget(QWidget):
    """Custom menu widget with pinning checkbox and action trigger."""
    def __init__(self, item, item_id, is_hidden, on_toggle_pin, parent=None):
        super().__init__(parent)
        self.item = item
        self.item_id = item_id
        self.on_toggle_pin = on_toggle_pin
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(10)
        
        # 1. Pin Checkbox
        self.chk = QCheckBox()
        self.chk.setChecked(not is_hidden)
        self.chk.setToolTip("Pin to Toolbar")
        self.chk.stateChanged.connect(lambda state: self.on_toggle_pin(self.item_id, state == Qt.CheckState.Checked.value))
        layout.addWidget(self.chk)
        
        # 2. Action Trigger (Icon + Name)
        self.btn = QPushButton()
        self.btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn.setStyleSheet("QPushButton { text-align: left; background: transparent; border: none; padding: 4px; border-radius: 4px; } QPushButton:hover { background: rgba(0,0,0,0.05); }")
        
        if isinstance(item, QAction):
            self.btn.setIcon(item.icon())
            self.btn.setText(item.text() or item.toolTip())
            self.btn.clicked.connect(item.trigger)
        elif isinstance(item, QWidget):
            self.btn.setText(item.toolTip() or "Widget")
            # For widgets, clicking just selects/focuses them if possible, or triggers primary action
            if hasattr(item, 'clicked'): self.btn.clicked.connect(item.clicked)
            
        layout.addWidget(self.btn, 1)
        
    def _apply_theme(self, mode):
        c = styles.ZEN_THEME.get(mode, styles.ZEN_THEME["light"])
        fg = c['foreground']
        accent = c['accent']
        self.btn.setStyleSheet(f"QPushButton {{ color: {fg}; text-align: left; background: transparent; border: none; padding: 4px; border-radius: 4px; }} QPushButton:hover {{ background: {accent}; }}")
        # Checkbox indicator handle via QMenu stylesheet usually, but here it's an embedded widget

class CustomTitleBar(QWidget):
    """
    A custom frameless title bar that hosts:
    1. App Icon & Title
    2. Editor Toolbar Actions (Centered/Stretched) - NOW WITH MORE TOOLS
    3. Window Controls (Min, Max, Close)
    """
        
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(20, 0, 10, 0) # Increased left margin for alignment
        self.layout.setSpacing(4)
        self.setFixedHeight(40) # Standard sleek height
        
        # Settings for persistence
        self.settings = QSettings("ZenNotes", "ToolbarSettings")
        self.hidden_action_ids = set(self.settings.value("hidden_items", [], type=list))
        self.all_items_ref = [] # Keep reference to recreate toolbar
        self.more_tools_btn = None # Track the button to rescue widgets
        
        # Editor Toolbar Container (Left aligned)
        self.toolbar_container = QWidget()
        self.toolbar_layout = QHBoxLayout(self.toolbar_container)
        self.toolbar_layout.setContentsMargins(0, 0, 0, 0)
        self.toolbar_layout.setSpacing(4)
        self.toolbar_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        # SCROLL AREA WRAPPER to prevent overflow cutting off window controls
        self.toolbar_scroll = QScrollArea()
        self.toolbar_scroll.setWidget(self.toolbar_container)
        self.toolbar_scroll.setWidgetResizable(True)
        self.toolbar_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.toolbar_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.toolbar_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        # Transparent background for scroll area
        self.toolbar_scroll.setStyleSheet("background: transparent;")
        
        self.layout.addWidget(self.toolbar_scroll, 1) # Stretch factor 1 to take available space
        
        # Spacer to push window controls to right
        self.right_spacer = QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.layout.addItem(self.right_spacer)

        # 3. Window Controls
        self.btn_min = self._create_window_btn("window_minimize", self.minimize_window, "Minimize")
        self.btn_max = self._create_window_btn("window_maximize", self.toggle_maximize, "Maximize")
        self.btn_close = self._create_window_btn("window_close", self.close_window, "Close", is_close=True)
        
        # Dragging State
        self._drag_pos = None
        
        # Cache for QWidgetActions to prevent widget deletion
        self.widget_actions = {}

    def _create_window_btn(self, icon_name, callback, tooltip, is_close=False):
        # Use QToolButton for better icon centering and behavior
        btn = QToolButton()
        btn.setFixedSize(40, 32) # Wider for easier clicking
        btn.setToolTip(tooltip)
        btn.clicked.connect(callback)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Store icon name for theme refreshing
        btn.setProperty("icon_name", icon_name)
        btn.setProperty("is_close", is_close)
        
        self.layout.addWidget(btn)
        return btn

    def set_editor_toolbar_actions(self, actions):
        """Populate the center toolbar area with actions from the editor."""
        self.all_items_ref = actions
        self.repopulate_toolbar()

    def repopulate_toolbar(self):
        """Rebuilds the toolbar based on hidden items."""
        
        # 1. RECLAIM & FILTER WIDGETS
        valid_items = []
        for item in self.all_items_ref:
            if isinstance(item, QWidget):
                try:
                    item.setParent(self) 
                    item.setVisible(False)
                    valid_items.append(item)
                except RuntimeError:
                    continue
            else:
                valid_items.append(item)
                
        # 2. CLEAR LAYOUT
        while self.toolbar_layout.count():
            child = self.toolbar_layout.takeAt(0)
            if child.widget():
                child.widget().setParent(None)
        
        # 3. BUILD
        hidden_items = []
        last_was_separator = True # Start with true to avoid leading separator
        
        for item in valid_items:
            if item == "SEPARATOR":
                if not last_was_separator:
                    self._add_separator()
                    last_was_separator = True
                continue
                
            item_id = self._get_item_id(item)
            if item_id in self.hidden_action_ids:
                hidden_items.append(item)
                continue
                
            # Add to Toolbar
            self._add_toolbar_item(item, item_id)
            last_was_separator = False

        # 4. ADD "MORE TOOLS" IF NEEDED
        if hidden_items:
            self._add_more_tools_btn(hidden_items)
            
        self.toolbar_container.update()

    def _get_item_id(self, item):
        try:
            if isinstance(item, QWidget): return item.toolTip()
            if isinstance(item, QAction): return item.toolTip() or item.text()
        except RuntimeError: return None
        return None

    def _toggle_pin(self, item_id, checked):
        """Callback from More Tools menu checkboxes."""
        if checked:
            if item_id in self.hidden_action_ids:
                self.hidden_action_ids.remove(item_id)
        else:
            self.hidden_action_ids.add(item_id)
        self._save_settings()
        self.repopulate_toolbar()

    def _add_separator(self):
        line = QLabel()
        line.setFixedWidth(1)
        line.setFixedHeight(16)
        line.setProperty("class", "ToolbarSeparator")
        # Apply current theme style immediately if possible
        if self.property("theme_mode"):
             c = styles.ZEN_THEME.get(self.property("theme_mode"), styles.ZEN_THEME["light"])
             line.setStyleSheet(f"background-color: {c['border']};")
        self.toolbar_layout.addWidget(line)

    def _add_toolbar_item(self, item, item_id):
        widget = None
        
        if isinstance(item, QWidget):
            item.setVisible(True) # Unhide after reclamation
            self.toolbar_layout.addWidget(item)
            widget = item
            if "Level" in item.toolTip():
                print(f"DEBUG: Adding Toolbar Item: {item} (ToolTip: {item.toolTip()}) - Visible? {item.isVisible()} - Size: {item.size()}")
            # Apply appropriate style based on type
            if isinstance(item, (QComboBox, QSpinBox)):
                item.setStyleSheet(self._get_input_style(self.property("theme_mode") or "light"))
            elif isinstance(item, QToolButton):
                item.setStyleSheet(self._get_toolbar_btn_style(self.property("theme_mode") or "light"))
                
        elif isinstance(item, QAction):
            # Create a tool button for the action for automatic syncing
            btn = QToolButton()
            btn.setDefaultAction(item)
            btn.setFixedSize(32, 28) # Standardized larger size
            btn.setIconSize(QSize(20, 20)) # Standardized icon size
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
            
            # Apply Style
            btn.setProperty("class", "ToolbarBtn")
            btn.setStyleSheet(self._get_toolbar_btn_style(self.property("theme_mode") or "light"))
            
            self.toolbar_layout.addWidget(btn)
            widget = btn

        # Add Context Menu for Hiding
        if widget and item_id:
            widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            # Safe disconnect
            try: widget.customContextMenuRequested.disconnect()
            except: pass
            widget.customContextMenuRequested.connect(lambda pos, i=item_id: self._show_context_menu(pos, i))

    def _show_context_menu(self, pos, item_id):
        menu = QMenu(self)
        hide_action = QAction("Hide from Toolbar", self)
        hide_action.triggered.connect(lambda: self._hide_item(item_id))
        menu.addAction(hide_action)
        
        customize_action = QAction("Customize Toolbar...", self)
        customize_action.triggered.connect(self.open_customize_dialog)
        menu.addAction(customize_action)
        
        menu.exec(QCursor.pos())

    def _hide_item(self, item_id):
        if item_id:
            self.hidden_action_ids.add(item_id)
            self._save_settings()
            self.repopulate_toolbar()

    def _save_settings(self):
        self.settings.setValue("hidden_items", list(self.hidden_action_ids))

    def _add_more_tools_btn(self, hidden_items):
        btn = QToolButton()
        # Ensure we keep a reference
        self.more_tools_btn = btn
        
        # Use premium icon instead of text ellipsis
        mode = self.property("theme_mode") or "light"
        is_dark = mode in ("dark", "dark_blue", "ocean_depth", "noir_ember")
        c = styles.ZEN_THEME.get(mode, styles.ZEN_THEME["light"])
        btn_color = "#FFFFFF" if is_dark else c['muted_foreground']
        
        btn.setIcon(get_premium_icon("more_vertical", color=btn_color))
        btn.setIconSize(QSize(20, 20))
        btn.setToolTip("More Tools")
        btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        btn.setFixedSize(32, 28) # Standardized with other toolbar actions
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(self._get_toolbar_btn_style(mode))
        
        # Store for theme refreshing
        btn.setProperty("icon_name", "more_vertical")
        
        menu = QMenu(btn)
        menu.setStyleSheet(self._get_menu_style(mode))
        
        # Populate with hidden items
        for item in hidden_items:
            item_id = self._get_item_id(item)
            action = QWidgetAction(self)
            
            row = ToolbarActionWidget(item, item_id, True, self._toggle_pin, self)
            row._apply_theme(mode)
            
            action.setDefaultWidget(row)
            menu.addAction(action)
                
        menu.addSeparator()
        cust_action = QAction("Customize Toolbar...", self)
        cust_action.triggered.connect(self.open_customize_dialog)
        menu.addAction(cust_action)
        
        btn.setMenu(menu)
        self.toolbar_layout.addWidget(btn)

    def open_customize_dialog(self):
        dlg = CustomizeToolbarDialog(self.all_items_ref, self.hidden_action_ids, self)
        if dlg.exec():
            new_hidden = dlg.get_hidden_ids()
            self.hidden_action_ids = set(new_hidden)
            self._save_settings()
            self.repopulate_toolbar()

    # Window Control Actions
    def minimize_window(self):
        self.window().showMinimized()

    def toggle_maximize(self):
        if self.window().isMaximized():
            self.window().showNormal()
            self.btn_max.setText("☐")
        else:
            self.window().showMaximized()
            self.btn_max.setText("❐")

    def close_window(self):
        self.window().close()

    # Dragging Logic
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos:
            delta = event.globalPosition().toPoint() - self._drag_pos
            self.window().move(self.window().pos() + delta)
            self._drag_pos = event.globalPosition().toPoint()
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        
    def mouseDoubleClickEvent(self, event):
        # Maximize on double click
        self.toggle_maximize()

    def _get_toolbar_btn_style(self, mode="light"):
        c = styles.ZEN_THEME.get(mode, styles.ZEN_THEME["light"])
        
        # Zen-focused styling: Subtle interaction, powerful active state
        # Hover: Slight tint of primary color
        # Checked: Solid subtle primary background
        
        is_dark = mode in ("dark", "dark_blue", "ocean_depth", "noir_ember")
        
        # Opacities for Zen feel
        active_bg = c.get('active_item_bg', "rgba(0,0,0,0.1)")
        accent_bg = c['accent']
        
        return f"""
            QPushButton, QToolButton {{
                background: transparent;
                border: 1px solid transparent;
                border-radius: 10px; /* Enhanced Rounded Box */
                padding: 4px;
                margin: 0px 1px;
            }}
            QPushButton::menu-indicator, QToolButton::menu-indicator {{
                image: none;
            }}
            
            /* Powerful Hover: Accent background + Primary Border hint */
            QPushButton:hover, QToolButton:hover {{
                background-color: {c['elevated']}; /* Pop out slightly */
                border: 1px solid {c['border']};
            }}
            
            /* Pressed/Checked: "Zen Mode" Active State */
            QPushButton:checked, QToolButton:checked, QPushButton:pressed {{
                background-color: {active_bg};
                color: {c['primary']}; /* Colorize icon/text */
                border: 1px solid {c['primary']};
            }}
            
            QToolButton::menu-button {{
                border: none;
                width: 16px;
                background: transparent;
            }}
        """

    def _get_input_style(self, mode="light"):
        c = styles.ZEN_THEME.get(mode, styles.ZEN_THEME["light"])
        
        return f"""
            QComboBox, QSpinBox {{
                background-color: {c['card']}; /* Card background for depth */
                color: {c['foreground']};
                border: 1px solid {c['input']};
                border-radius: 10px;
                padding: 4px 8px;
                font-family: "Inter", sans-serif;
                font-size: 12px;
                min-height: 22px;
            }}
            QComboBox:hover, QSpinBox:hover {{
                border: 1px solid {c['primary']}; /* Zen Focus */
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                border: none;
                background: transparent;
                width: 16px;
            }}
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
                background-color: {c['accent']};
                border-radius: 2px;
            }}
        """
    
    def _get_menu_style(self, mode="light"):
        c = styles.ZEN_THEME.get(mode, styles.ZEN_THEME["light"])
        return f"""
            QMenu {{
                background-color: {c['background']};
                color: {c['foreground']};
                border: 1px solid {c['border']};
                border-radius: 8px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 6px 20px 6px 12px;
                border-radius: 6px;
                margin: 2px 4px;
                font-family: "Inter", sans-serif;
                font-size: 13px;
            }}
            QMenu::item:selected {{
                background-color: {c['accent']};
                color: {c['accent_foreground']};
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {c['border']};
                margin: 4px 8px;
            }}
        """

    def set_theme_mode(self, mode):
        """Update styles based on theme."""
        self.setProperty("theme_mode", mode) 
        is_dark = mode in ("dark", "dark_blue", "ocean_depth", "noir_ember")
        c = styles.ZEN_THEME.get(mode, styles.ZEN_THEME["light"])
        
        # 1. Main Bar - Zen Clarity
        # We can add a subtle gradient or solid standard background. 
        # User asked for "Zen mode color for the toolbar properly".
        # Let's align it with the Sidebar/Card look if possible, or keep it distinct.
        # Maybe use 'card' background for the toolbar scroll area?
        
        self.setStyleSheet(f"""
            CustomTitleBar {{
                background-color: {c['background']}; 
                border-bottom: 1px solid {c['border']};
            }}
            QLabel.ToolbarSeparator {{
                background-color: {c['border']};
                margin: 0px 4px; /* More spacing around separators */
            }}
            QScrollArea {{
                border: none;
                background: transparent;
            }}
            QMenu {{
                background-color: {c['background']};
                color: {c['foreground']};
                border: 1px solid {c['border']};
                border-radius: 8px;
                padding: 4px;
            }}
        """)
        
        # 2. Window Control Buttons
        btn_color = "#FFFFFF" if is_dark else c['muted_foreground'] 
        print(f"DEBUG: title_bar.set_theme_mode mode='{mode}', is_dark={is_dark}, btn_color='{btn_color}'")
        hover_bg = c['destructive'] # Close button red
        
        # Refresh Icons with current color
        self.btn_min.setIcon(get_premium_icon("window_minimize", color=btn_color))
        
        max_icon = "window_restore" if self.window().isMaximized() else "window_maximize"
        self.btn_max.setIcon(get_premium_icon(max_icon, color=btn_color))
        self.btn_max.setProperty("icon_name", max_icon) # Update property for state tracking
        
        # Close button icon is white on red hover, so we handle that in stylesheet or just keep it simple.
        # Let's keep it monochromatic for now.
        self.btn_close.setIcon(get_premium_icon("window_close", color=btn_color))

        win_btn_style = f"""
            QToolButton {{
                background: transparent;
                border: none;
                border-radius: 0px; 
            }}
            QToolButton:hover {{
                background: {c['accent']};
            }}
        """
        self.btn_min.setStyleSheet(win_btn_style)
        self.btn_max.setStyleSheet(win_btn_style)
        
        # Close button has unique red hover
        close_style = f"""
            QToolButton {{
                background: transparent;
                border: none;
                border-radius: 0px; 
            }}
            QToolButton:hover {{
                background: {c['destructive']};
                /* We can't easily change icon color on hover via stylesheet for QIcon. 
                   But standard Windows behavior: Close becomes Red BG, White Icon.
                   Since our icon is SVG derived, it's static in the button.
                   We'd need backend logic to swap icon on hover, or just Accept that the icon 
                   stays the 'btn_color'. If btn_color is dark (light mode), it might clash with red bg.
                   However, usually close button hover text is White. 
                   If we really want premium, we should swap icon on hover events. 
                   For now, let's just make sure it looks okay. */
            }}
        """
        self.btn_close.setStyleSheet(close_style)

        # 3. Toolbar Widgets
        toolbar_style = self._get_toolbar_btn_style(mode)
        input_style = self._get_input_style(mode)
        
        for i in range(self.toolbar_layout.count()):
            item = self.toolbar_layout.itemAt(i)
            widget = item.widget()
            if not widget: continue
            
            if isinstance(widget, (QPushButton, QToolButton)):
                widget.setStyleSheet(toolbar_style)
                # Refresh icon if name is stored (e.g. for More Tools btn)
                if isinstance(widget, QToolButton) and widget.property("icon_name"):
                    widget.setIcon(get_premium_icon(widget.property("icon_name"), color=btn_color))
            elif isinstance(widget, (QComboBox, QSpinBox)):
                widget.setStyleSheet(input_style)
            elif widget.property("class") == "ToolbarSeparator":
                widget.setStyleSheet(f"background-color: {c['border']}; margin: 0px 4px;")
