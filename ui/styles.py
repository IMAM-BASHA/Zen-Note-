from util.theme_utils import convert_theme_color

# Base Light Theme Definition (Semantic Tokens)
LIGHT_THEME_BASE = {
    "window_bg": "#FFFFFF",
    "window_text": "#333333",
    "sidebar_bg": "#F3F3F3",
    "sidebar_text": "#333333",
    "sidebar_header_bg": "#F3F3F3",
    "item_selected_bg": "#E0E0E0",
    "item_selected_text": "#000000",
    "item_hover_bg": "#E8E8E8",
    "item_border": "#E0E0E0",
    "editor_bg": "#FFFFFF",
    "editor_text": "#333333",
    "editor_selection": "#007ACC",
    "splitter_handle": "#D3D3D3",
    "button_bg": "#E0E0E0",
    "button_text": "#333333",
    "button_hover": "#D0D0D0",
    "button_pressed": "#C0C0C0",
    "input_bg": "#FFFFFF",
    "input_border": "#CCCCCC",
    "menu_bg": "#F3F3F3",
    "scrollbar_bg": "#F0F0F0",
    "scrollbar_handle": "#C0C0C0",
    "syntax_keyword": "#0000FF",
    "highlight_bg_base": "#FFF176",
    "link_color": "#007ACC"
}

# Automatically Generate Dark Theme using HSL Transformation
DARK_THEME_GENERATED = {}
for key, value in LIGHT_THEME_BASE.items():
    if value.startswith("#"):
        DARK_THEME_GENERATED[key] = convert_theme_color(value, mode="dark")
    else:
        DARK_THEME_GENERATED[key] = value

# Manual Overrides for specific Dark Mode tokens if HSL math isn't perfect
# e.g., We might want a specific dark grey for background instead of calculated one
DARK_THEME_GENERATED["window_bg"] = "#121212" # Enforce standard dark bg
DARK_THEME_GENERATED["editor_bg"] = "#1e1e1e" # VS Code Dark
DARK_THEME_GENERATED["syntax_keyword"] = "#569CD6" # Keep VS Code Blue
DARK_THEME_GENERATED["editor_selection"] = "#264f78" # Better contrast selection

THEME_COLORS = {
    "light": LIGHT_THEME_BASE,
    "dark": DARK_THEME_GENERATED
}

def get_stylesheet(mode="light"):
    # Fallback to light if mode not found
    colors = THEME_COLORS.get(mode, THEME_COLORS["light"])
    
    return f"""
        /* Main Window */
        QMainWindow, #MainContainer {{
            background-color: {colors['window_bg']};
            color: {colors['window_text']};
            font-family: -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            font-size: 14px;
        }}

        /* Sidebar */
        QWidget#SidebarHeader {{
            background-color: {colors['sidebar_header_bg']};
            color: {colors['sidebar_text']};
            font-weight: bold;
            font-size: 16px;
        }}
        /* Sidebar Tree */
        QTreeWidget {{
            background-color: {colors['sidebar_bg']};
            color: {colors['window_text']};
            border: none;
            outline: none;
        }}
        QTreeWidget::item {{
            padding: 8px 5px;
            border-bottom: 1px solid {colors['item_border']};
        }}
        QTreeWidget::item:selected {{
            background-color: {colors['item_selected_bg']};
            color: {colors['item_selected_text']};
            border-left: 3px solid {colors['editor_selection']};
        }}
        QTreeWidget::item:hover {{
            background-color: {colors['item_hover_bg']};
        }}
        QTreeWidget::branch {{
            background-color: {colors['sidebar_bg']};
        }}
        QTreeWidget::branch:has-children:!has-siblings:closed,
        QTreeWidget::branch:closed:has-children:has-siblings {{
            border-image: none;
            image: url(util/icons/chevron-right.png); /* Fallback to standard if needed */
        }}
        QTreeWidget::branch:open:has-children:!has-siblings,
        QTreeWidget::branch:open:has-children:has-siblings {{
            border-image: none;
            image: url(util/icons/chevron-down.png);
        }}

        /* Editor */
        QTextEdit {{
            background-color: {colors['editor_bg']};
            color: {colors['editor_text']};
            border: none;
            padding: 15px;
            selection-background-color: {colors['editor_selection']};
            selection-color: white;
        }}
        
        /* Syntax Highlighting CSS Classes (Dynamic) */
        .kn {{ color: {colors['syntax_keyword']}; font-weight: bold; }} /* Keyword.Namespace */
        .k  {{ color: {colors['syntax_keyword']}; font-weight: bold; }} /* Keyword */
        .s  {{ color: #CD9178; }} /* String (constant for now, can be dynamic) */
        .c  {{ color: #6A9955; font-style: italic; }} /* Comment */
        
        /* Highlight fixes */
        QTextEdit {{
            color: {colors['editor_text']};
        }}

        /* Splitter */
        QSplitter::handle {{
            background-color: {colors['splitter_handle']};
        }}

        /* Buttons (General) */
        QPushButton {{
            background-color: {colors['button_bg']};
            color: {colors['button_text']};
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
        }}
        QPushButton:hover {{
            background-color: {colors['button_hover']};
        }}
        QPushButton:pressed {{
            background-color: {colors['button_pressed']};
        }}
        QPushButton:checked {{
            background-color: {colors['editor_selection']};
            color: white;
        }}
        
        /* Specific Button Overrides */
        QPushButton#NewFolderBtn, QPushButton#NewNoteBtn {{
            background-color: #007ACC;
            color: white;
            font-weight: bold;
        }}
        QPushButton#NewFolderBtn:hover, QPushButton#NewNoteBtn:hover {{
            background-color: #008AD8;
        }}

        /* Inputs */
        QLineEdit {{
            background-color: {colors['input_bg']};
            color: {colors['window_text']};
            border: 1px solid {colors['input_border']};
            padding: 5px;
            border-radius: 3px;
        }}
        
        /* Scrollbars (Native usually fine, but consistent logic) */
        QScrollBar:vertical {{
            border: none;
            background: {colors['scrollbar_bg']};
            width: 10px;
        }}
        QScrollBar::handle:vertical {{
            background: {colors['scrollbar_handle']};
            min-height: 20px;
            border-radius: 5px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            border: none;
            background: none;
        }}

        /* Menu */
        QMenu {{
            background-color: {colors['menu_bg']};
            color: {colors['window_text']};
            border: 1px solid {colors['input_border']};
        }}
        QMenu::item:selected {{
            background-color: {colors['editor_selection']};
            color: white;
        }}

        /* ComboBox */
        QComboBox {{
            background-color: {colors['input_bg']};
            color: {colors['window_text']};
            border: 1px solid {colors['input_border']};
            padding: 5px;
            border-radius: 3px;
        }}
        QComboBox::drop-down {{
            border: none;
        }}
        QComboBox QAbstractItemView {{
            background-color: {colors['menu_bg']};
            color: {colors['window_text']};
            selection-background-color: {colors['editor_selection']};
            selection-color: white;
            border: 1px solid {colors['input_border']};
        }}
    """
