# SHADCN-UI INSPIRED THEME SYSTEM (Zinc Palette)
# Replicating the clean, neutral, and professional look of Vercel's design system.

# ZEN NOTES THEME SYSTEM
# "Creative Amber" (Dark) & "Zen Clarity" (Light)

ZEN_THEME = {
    "light": {
        "background": "#F9F8F6",      # background-light (Warm White)
        "foreground": "#3D3A38",      # text-main (Dark Taupe)
        "card": "#FFFFFF",            # surface-light
        "card_foreground": "#3D3A38",
        "popover": "#FFFFFF",
        "popover_foreground": "#3D3A38",
        "primary": "#7B9E87",         # Sage Green
        "primary_foreground": "#FFFFFF",
        "secondary": "#E8E6E4",       # taupe-light
        "secondary_foreground": "#3D3A38",
        "muted": "#F2F0ED",           # Slightly darker than bg
        "muted_foreground": "#8D8682",# taupe
        "accent": "#E8E6E4",          # taupe-light (Hover)
        "accent_foreground": "#3D3A38",
        "destructive": "#ef4444",
        "destructive_foreground": "#fafafa",
        "border": "#E0DDD9",          # border-light
        "input": "#E0DDD9",
        "ring": "#7B9E87",            # Sage
        "sidebar_bg": "#FFFFFF",      # surface-light
        "sidebar_fg": "#3D3A38",
        "sidebar_border": "#E0DDD9",
        "active_item_bg": "rgba(123, 158, 135, 0.15)", # Sage Dim
        "selection_bg": "#E8E6E4",
        "selection_fg": "#3D3A38",
        "scrollbar_bg": "#F9F8F6",
        "scrollbar_handle": "#D1CEC9",
        "elevated": "#FFFFFF",
        "shadow": "rgba(0, 0, 0, 0.05)" # shadow-soft
    },
    "dark": {
        "background": "#1C1917",      # background-dark (Stone 900)
        "foreground": "#E7E5E4",      # Stone 200 / Text
        "card": "#292524",            # surface-dark (Stone 800)
        "card_foreground": "#E7E5E4",
        "popover": "#292524",
        "popover_foreground": "#E7E5E4",
        "primary": "#D97706",         # Amber 600
        "primary_foreground": "#FFFFFF",
        "secondary": "#292524",       # Stone 800
        "secondary_foreground": "#E7E5E4",
        "muted": "#292524",
        "muted_foreground": "#A8A29E",# Stone 400
        "accent": "rgba(217, 119, 6, 0.1)", # amber-dim
        "accent_foreground": "#D97706", # Amber Text
        "destructive": "#ef4444",
        "destructive_foreground": "#fafafa",
        "border": "#44403C",          # Stone 700 (adjusted for visibility)
        "input": "#292524",
        "ring": "#D97706",
        "sidebar_bg": "#0C0A09",      # surface-darker (Stone 950)
        "sidebar_fg": "#E7E5E4",
        "sidebar_border": "#1C1917",
        "active_item_bg": "rgba(217, 119, 6, 0.1)", # amber-dim
        "selection_bg": "#451a03",    # Deep Amber/Brown
        "selection_fg": "#E7E5E4",
        "scrollbar_bg": "#1C1917",
        "scrollbar_handle": "#44403C",
        "elevated": "#292524",
        "shadow": "rgba(0, 0, 0, 0.5)"
    },
    "dark_blue": {
        "background": "#0F172A",      # Slate 900 (Main BG)
        "foreground": "#F1F5F9",      # Slate 100 (Text)
        "card": "#1E293B",            # Slate 800 (Card/Input)
        "card_foreground": "#F1F5F9",
        "popover": "#1E293B",
        "popover_foreground": "#F1F5F9",
        "primary": "#38BDF8",         # Sky 400 (Branding/Accents)
        "primary_foreground": "#0F172A",
        "secondary": "#334155",       # Slate 700
        "secondary_foreground": "#F1F5F9",
        "muted": "#1E293B",
        "muted_foreground": "#94A3B8",# Slate 400
        "accent": "rgba(56, 189, 248, 0.15)", # Sky Dim
        "accent_foreground": "#38BDF8",
        "destructive": "#EF4444",     # Red 500
        "destructive_foreground": "#FFFFFF",
        "border": "#334155",          # Slate 700
        "input": "#1E293B",
        "ring": "#38BDF8",
        "sidebar_bg": "#020617",      # Slate 950 (Sidebar)
        "sidebar_fg": "#F1F5F9",
        "sidebar_border": "#1E293B",
        "active_item_bg": "rgba(14, 165, 233, 0.2)", # Sky 500 Dim
        "selection_bg": "#0369A1",    # Sky 700
        "selection_fg": "#FFFFFF",
        "scrollbar_bg": "#0F172A",
        "scrollbar_handle": "#334155",
        "elevated": "#1E293B",
        "shadow": "rgba(0, 0, 0, 0.5)"
    },
    "rose": {
        "background": "#FFFAF0",      # Floral White / Cream (Main BG)
        "foreground": "#4A044E",      # Deep Purple/Brown text
        "card": "#FFFFFF",            # White
        "card_foreground": "#4A044E",
        "popover": "#FFF1F2",
        "popover_foreground": "#881337",
        "primary": "#BE185D",         # Pink 700 (Strong Rose)
        "primary_foreground": "#FFFFFF",
        "secondary": "#FCE7F3",       # Pink 100
        "secondary_foreground": "#831843",
        "muted": "#FFF1F2",
        "muted_foreground": "#9D174D",# Pink 800
        "accent": "rgba(190, 24, 93, 0.1)", # Rose Dim
        "accent_foreground": "#BE185D",
        "destructive": "#9F1239",     # Rose 800
        "destructive_foreground": "#FFFFFF",
        "border": "#FBCFE8",          # Pink 200
        "input": "#FFFFFF",
        "ring": "#BE185D",
        "sidebar_bg": "#FDF2F8",      # Pink 50 (Sidebar - distinct from main)
        "sidebar_fg": "#831843",      # Pink 900
        "sidebar_border": "#FBCFE8",  # Pink 200
        "active_item_bg": "rgba(190, 24, 93, 0.15)",
        "selection_bg": "#DB2777",    # Pink 600
        "selection_fg": "#FFFFFF",
        "scrollbar_bg": "#FFF1F2",
        "scrollbar_handle": "#FECDD3",
        "elevated": "#FFFFFF",
        "shadow": "rgba(0, 0, 0, 0.05)"
    }
}

# Compatibility Alias
SHADCN_ZINC = ZEN_THEME

def get_stylesheet(mode="light"):
    c = ZEN_THEME.get(mode, ZEN_THEME["light"])
    
    # Common radius and font settings
    radius = "12px" # Rounded styling from reference
    
    # Premium Typography System
    # 1. Inter: engineered for screens, neutral and efficient.
    font = 'font-family: "Inter", "Segoe UI", "Roboto", "Helvetica Neue", "Arial", sans-serif;'
    # 2. Playfair Display: academic, sophisticated, and traditional.
    display_font = 'font-family: "Playfair Display", "Constantia", "Sitka Heading", "Cambria", "Georgia", serif;'
    # 3. IBM Plex Mono: technical precision and offline craftsmanship.
    mono_font = 'font-family: "IBM Plex Mono", "JetBrains Mono", "Consolas", "Monaco", monospace;'
    
    return f"""
        /* GLOBAL RESET & TYPOGRAPHY */
        * {{
            {font}
            outline: none;
        }}
        
        QMainWindow, QWidget#MainContainer, QDialog {{
            background-color: {c['background']};
            color: {c['foreground']};
        }}

        /* --- SIDEBAR --- */
        QWidget#Sidebar {{
            background-color: {c['sidebar_bg']};
            border-right: 1px solid {c['sidebar_border']};
        }}
        QWidget#SidebarHeader {{
            background-color: transparent;
            color: {c['sidebar_fg']};
            padding: 0px; 
        }}
        QLabel#SidebarTitle {{
            color: {c['sidebar_fg']};
            {display_font}
            font-weight: 700;
            font-size: 18px; 
            letter-spacing: 0.02em;
            text-transform: uppercase;
        }}
        
        QFrame#SidebarLogoContainer {{
            background-color: {c['active_item_bg']};
            border: 1px solid {c['border']};
            border-radius: 8px;
        }}
        
        /* Tree Widget (Sidebar Items) */
        QTreeWidget {{
            background-color: transparent;
            color: {c['sidebar_fg']};
            border: none;
            padding: 4px;
            selection-background-color: {c['active_item_bg']};
            selection-color: {c['primary'] if mode == 'light' else '#ffffff'};
        }}
        QTreeWidget::item {{
            padding: 6px 12px;
            border-radius: {radius};
            margin-bottom: 2px;
            color: {c['sidebar_fg']};
            font-family: "Inter", sans-serif;
            font-size: 14px;
        }}
        QTreeWidget::item:hover {{
            background-color: {c['accent']};
            color: {c['accent_foreground']};
        }}
        QTreeWidget::item:selected {{
            background-color: {c['active_item_bg']};
            color: {c['primary'] if mode == 'light' else '#ffffff'};
            font-weight: 600;
        }}
        
        /* NOTE LIST - CARD STYLE */
        QListWidget {{
            background-color: {c['background']};
            border: none;
            color: {c['foreground']};
            padding: 8px;
            selection-background-color: transparent; 
            outline: none;
            font-family: "Inter", sans-serif;
            font-size: 13px;
        }}
        QListWidget::item {{
            background-color: {c['card']};
            border: 1px solid {c['border']};
            border-radius: {radius};
            padding: 12px;
            margin-bottom: 8px;
            color: {c['foreground']};
            font-family: "Inter", sans-serif;
        }}
        QListWidget::item:selected {{
            background-color: {c['active_item_bg']};
            color: {c['primary'] if mode == 'light' else c['primary']}; /* Zen uses Primary color for text in both modes */
            border: 1px solid {c['primary']};
        }}
        QListWidget::item:hover {{
            background-color: {c['elevated']};
            border-color: {c['primary']}; /* Use Primary border on hover for gloss */
        }}

        /* --- EDITOR --- */
        QTextEdit {{
            background-color: {c['background']};
            color: {c['foreground']};
            border: none;
            padding: 32px; /* More breathable workspace */
            selection-background-color: {c.get('selection_bg', c['secondary'])};
            selection-color: {c.get('selection_fg', c['secondary_foreground'])};
            line-height: 1.7; /* Optical sizing */
        }}

        /* --- BUTTONS (Shadcn Variants) --- */
        /* BUTTONS - ANIMATED FEEL */
        QPushButton {{
            background-color: transparent;
            color: {c['foreground']};
            border: 1px solid transparent;
            border-radius: {radius};
            padding: 6px 12px;
            font-weight: 500;
        }}
        QPushButton:hover {{
            background-color: {c['accent']};
            color: {c['accent_foreground']};
            border: 1px solid {c['border']};
        }}
        QPushButton:pressed {{
            background-color: {c['input']};
            margin-top: 1px;
            margin-left: 1px;
        }}
        
        /* Primary Action Buttons (e.g. New Note) - User should set ObjectName 'PrimaryBtn' */
        QPushButton#PrimaryBtn, QPushButton#NewNoteBtn, QPushButton#NewFolderBtn {{
            background-color: {c['primary']};
            color: {c['primary_foreground']};
            border: 1px solid {c['primary']};
        }}
        QPushButton#PrimaryBtn:hover, QPushButton#NewNoteBtn:hover, QPushButton#NewFolderBtn:hover {{
            background-color: {c['primary']}; /* Shadcn usually typically opacity change, we'll shift slightly */
            border: 1px solid {c['primary']};
            opacity: 0.9;
        }}

        /* Destructive Buttons */
        QPushButton#DestructiveBtn {{
            background-color: {c['destructive']};
            color: {c['destructive_foreground']};
        }}

        /* View Toggle Button (Phase 45) */
        QPushButton#ViewToggleBtn {{
            background-color: {c['secondary']};
            border: 1px solid {c['border']};
            border-radius: 8px;
            padding: 4px;
        }}
        QPushButton#ViewToggleBtn:hover {{
            background-color: {c['accent']};
            border: 1px solid {c['primary']};
        }}

        /* --- INPUTS & DROPDOWNS --- */
        QLineEdit {{
            background-color: {c['background']};
            color: {c['foreground']};
            border: 1px solid {c['input']};
            border-radius: {radius};
            padding: 6px 12px;
            height: 32px;
            font-size: 13px;
        }}
        QLineEdit:focus {{
            border: 1px solid {c['ring']};
        }}

        QComboBox {{
            background-color: {c['background']};
            color: {c['foreground']};
            border: 1px solid {c['input']};
            border-radius: {radius};
            padding: 8px 12px; /* More padding */
        }}
        /* Specific styling for Sidebar Notebook Selector to look like a Card */
        QComboBox#SidebarNotebookSelector {{
            background-color: {c['card']};
            border: 1px solid {c['border']};
            font-weight: 600;
        }}
        QComboBox#SidebarNotebookSelector:hover {{
            border: 1px solid {c['primary']}; /* Active feel */
        }}

        QComboBox::drop-down {{
            border: none;
            width: 24px;
        }}
        QComboBox::down-arrow {{
            image: url(util/icons/chevron-down.png);
            width: 14px;
            height: 14px;
            margin-right: 8px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {c['popover']};
            color: {c['popover_foreground']};
            border: 1px solid {c['border']};
            border-radius: {radius};
            selection-background-color: {c['accent']};
            selection-color: {c['accent_foreground']};
            padding: 4px;
            outline: none;
        }}

        /* --- SCROLLBARS --- */
        QScrollBar:vertical {{
            background: {c['scrollbar_bg']};
            width: 10px;
            margin: 0px;
            border-radius: 0px;
        }}
        QScrollBar::handle:vertical {{
            background: {c['scrollbar_handle']};
            min-height: 24px;
            border-radius: 5px;
            margin: 2px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}

        /* --- MENUS --- */
        QMenu {{
            background-color: {c['popover']};
            color: {c['popover_foreground']};
            border: 1px solid {c['border']};
            border-radius: {radius};
            padding: 4px;
        }}
        QMenu::item {{
            padding: 6px 12px;
            border-radius: 4px;
        }}
        QMenu::item:selected {{
            background-color: {c['accent']};
            color: {c['accent_foreground']};
        }}
        
        /* SPLITTER */
        QSplitter::handle {{
            background-color: {c['border']};
            width: 1px; 
        }}
    """

