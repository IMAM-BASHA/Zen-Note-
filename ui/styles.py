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
    },
    "ocean_depth": {
        "background": "#0D1B2A",       # Deep Navy
        "foreground": "#E8F4F8",       # Soft White
        "card": "#1E3448",             # Dark Teal
        "card_foreground": "#E8F4F8",
        "popover": "#1E3448",
        "popover_foreground": "#E8F4F8",
        "primary": "#00B4D8",          # Electric Cyan
        "primary_foreground": "#0D1B2A",
        "secondary": "#1B2A3B",        # Slate Blue
        "secondary_foreground": "#E8F4F8",
        "muted": "#1B2A3B",
        "muted_foreground": "#7B9BB5", # Muted Blue-Gray
        "accent": "rgba(0, 180, 216, 0.12)",
        "accent_foreground": "#00B4D8",
        "destructive": "#EF4444",
        "destructive_foreground": "#FFFFFF",
        "border": "#243B55",           # Dark Blue
        "input": "#1E3448",
        "ring": "#00B4D8",
        "sidebar_bg": "#091422",       # Deeper Navy
        "sidebar_fg": "#E8F4F8",
        "sidebar_border": "#1B2A3B",
        "active_item_bg": "rgba(0, 180, 216, 0.15)",
        "selection_bg": "#0077B6",
        "selection_fg": "#FFFFFF",
        "scrollbar_bg": "#0D1B2A",
        "scrollbar_handle": "#243B55",
        "elevated": "#1E3448",
        "shadow": "rgba(0, 0, 0, 0.5)"
    },
    "forest_sage": {
        "background": "#F5F0E8",       # Warm Cream
        "foreground": "#1C2415",       # Deep Charcoal
        "card": "#FFFFFF",
        "card_foreground": "#1C2415",
        "popover": "#FFFFFF",
        "popover_foreground": "#1C2415",
        "primary": "#2D6A4F",          # Forest Green
        "primary_foreground": "#FFFFFF",
        "secondary": "#E8E2D5",        # Pale Sand
        "secondary_foreground": "#1C2415",
        "muted": "#EDE8DE",            # Soft Linen
        "muted_foreground": "#6B7C5A", # Muted Olive
        "accent": "rgba(45, 106, 79, 0.1)",
        "accent_foreground": "#2D6A4F",
        "destructive": "#C1292E",
        "destructive_foreground": "#FFFFFF",
        "border": "#C4CEB4",           # Light Sage
        "input": "#FFFFFF",
        "ring": "#2D6A4F",
        "sidebar_bg": "#EDE8DE",       # Soft Linen
        "sidebar_fg": "#1C2415",
        "sidebar_border": "#C4CEB4",
        "active_item_bg": "rgba(45, 106, 79, 0.12)",
        "selection_bg": "#2D6A4F",
        "selection_fg": "#FFFFFF",
        "scrollbar_bg": "#F5F0E8",
        "scrollbar_handle": "#C4CEB4",
        "elevated": "#FFFFFF",
        "shadow": "rgba(0, 0, 0, 0.06)"
    },
    "noir_ember": {
        "background": "#0A0A0A",       # True Black
        "foreground": "#F5F5F5",       # Off White
        "card": "#1E1E1E",             # Dark Gray
        "card_foreground": "#F5F5F5",
        "popover": "#1E1E1E",
        "popover_foreground": "#F5F5F5",
        "primary": "#E85D04",          # Burnt Orange
        "primary_foreground": "#FFFFFF",
        "secondary": "#141414",        # Charcoal
        "secondary_foreground": "#F5F5F5",
        "muted": "#141414",
        "muted_foreground": "#8A8A8A", # Warm Gray
        "accent": "rgba(232, 93, 4, 0.12)",
        "accent_foreground": "#E85D04",
        "destructive": "#DC2626",
        "destructive_foreground": "#FFFFFF",
        "border": "#2A2A2A",           # Dark Charcoal
        "input": "#1E1E1E",
        "ring": "#E85D04",
        "sidebar_bg": "#050505",       # Near Black
        "sidebar_fg": "#F5F5F5",
        "sidebar_border": "#1E1E1E",
        "active_item_bg": "rgba(232, 93, 4, 0.12)",
        "selection_bg": "#9A3412",
        "selection_fg": "#FFFFFF",
        "scrollbar_bg": "#0A0A0A",
        "scrollbar_handle": "#2A2A2A",
        "elevated": "#1E1E1E",
        "shadow": "rgba(0, 0, 0, 0.7)"
    },
    # Curated Gradient Themes
    "aurora_tide": {
        "background": "#0B1220",
        "window_gradient": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #071627, stop:0.52 #0B1E30, stop:1 #102A33)",
        "foreground": "#E6F6F7",
        "card": "#14263A",
        "card_foreground": "#E6F6F7",
        "popover": "#14263A",
        "popover_foreground": "#E6F6F7",
        "primary": "#22C7B8",
        "primary_foreground": "#082022",
        "primary_gradient": "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #14B8A6, stop:1 #38BDF8)",
        "primary_gradient_hover": "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0EA59B, stop:1 #22AEEA)",
        "secondary": "#173147",
        "secondary_foreground": "#E6F6F7",
        "muted": "#102537",
        "muted_foreground": "#8FB7C2",
        "accent": "rgba(20, 184, 166, 0.14)",
        "accent_foreground": "#7DEFE4",
        "destructive": "#EF4444",
        "destructive_foreground": "#FFFFFF",
        "border": "#22455C",
        "input": "#173147",
        "ring": "#22C7B8",
        "sidebar_bg": "#081624",
        "sidebar_gradient": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #081726, stop:1 #0D2230)",
        "sidebar_fg": "#E6F6F7",
        "sidebar_border": "#1C3A4E",
        "active_item_bg": "rgba(20, 184, 166, 0.18)",
        "selection_bg": "#0F766E",
        "selection_fg": "#FFFFFF",
        "scrollbar_bg": "#0B1220",
        "scrollbar_handle": "#22455C",
        "elevated": "#173147",
        "shadow": "rgba(0, 0, 0, 0.6)",
        "preview_gradient": ["#0A1A2B", "#103045", "#1C4C58"],
        "is_dark": True
    },
    "ember_dusk": {
        "background": "#17110D",
        "window_gradient": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #140F0A, stop:0.56 #26170F, stop:1 #18120F)",
        "foreground": "#F9EFE6",
        "card": "#261A14",
        "card_foreground": "#F9EFE6",
        "popover": "#261A14",
        "popover_foreground": "#F9EFE6",
        "primary": "#F59E0B",
        "primary_foreground": "#1F1309",
        "primary_gradient": "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #F59E0B, stop:1 #F97316)",
        "primary_gradient_hover": "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #E68C00, stop:1 #EA650F)",
        "secondary": "#302019",
        "secondary_foreground": "#F9EFE6",
        "muted": "#231813",
        "muted_foreground": "#C5A58D",
        "accent": "rgba(245, 158, 11, 0.14)",
        "accent_foreground": "#FBBF24",
        "destructive": "#EF4444",
        "destructive_foreground": "#FFFFFF",
        "border": "#4A3225",
        "input": "#302019",
        "ring": "#F59E0B",
        "sidebar_bg": "#120D0A",
        "sidebar_gradient": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #140E0B, stop:1 #1D140F)",
        "sidebar_fg": "#F9EFE6",
        "sidebar_border": "#3D2A20",
        "active_item_bg": "rgba(245, 158, 11, 0.18)",
        "selection_bg": "#C2410C",
        "selection_fg": "#FFFFFF",
        "scrollbar_bg": "#17110D",
        "scrollbar_handle": "#4A3225",
        "elevated": "#302019",
        "shadow": "rgba(0, 0, 0, 0.62)",
        "preview_gradient": ["#23170F", "#3A2416", "#522E15"],
        "is_dark": True
    },
    "pearl_mist": {
        "background": "#F4F7F7",
        "window_gradient": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #F7F9FF, stop:0.5 #EEF6F2, stop:1 #FFF7EC)",
        "foreground": "#1F2E35",
        "card": "#FFFFFF",
        "card_foreground": "#1F2E35",
        "popover": "#FFFFFF",
        "popover_foreground": "#1F2E35",
        "primary": "#0EA5A4",
        "primary_foreground": "#FFFFFF",
        "primary_gradient": "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0EA5A4, stop:1 #3B82F6)",
        "primary_gradient_hover": "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0C9391, stop:1 #2D73DF)",
        "secondary": "#E8EFF0",
        "secondary_foreground": "#1F2E35",
        "muted": "#F1F5F6",
        "muted_foreground": "#607981",
        "accent": "rgba(14, 165, 164, 0.12)",
        "accent_foreground": "#0F766E",
        "destructive": "#DC2626",
        "destructive_foreground": "#FFFFFF",
        "border": "#CAD8DC",
        "input": "#FFFFFF",
        "ring": "#0EA5A4",
        "sidebar_bg": "#F2F7F8",
        "sidebar_gradient": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #F4F8FB, stop:1 #EEF4F4)",
        "sidebar_fg": "#1F2E35",
        "sidebar_border": "#CAD8DC",
        "active_item_bg": "rgba(14, 165, 164, 0.14)",
        "selection_bg": "#0EA5A4",
        "selection_fg": "#FFFFFF",
        "scrollbar_bg": "#F4F7F7",
        "scrollbar_handle": "#B9CBD0",
        "elevated": "#FFFFFF",
        "shadow": "rgba(10, 26, 32, 0.08)",
        "preview_gradient": ["#F5FAFF", "#EEF6F2", "#FFF5EA"],
        "is_dark": False
    }
}

# Curated list shown in the Theme Chooser and used by keyboard theme cycling.
CURATED_THEME_ORDER = [
    "light",
    "forest_sage",
    "pearl_mist",
    "dark",
    "aurora_tide",
    "ember_dusk",
    "noir_ember",
]

# Map legacy or removed keys to curated replacements.
LEGACY_THEME_MAP = {
    "dark_blue": "aurora_tide",
    "ocean_depth": "aurora_tide",
    "rose": "pearl_mist",
}


def _normalize_hex(color):
    if not isinstance(color, str):
        return None
    s = color.strip()
    if not s.startswith("#"):
        return None
    s = s[1:]
    if len(s) == 3:
        s = "".join(ch * 2 for ch in s)
    if len(s) != 6:
        return None
    try:
        int(s, 16)
    except ValueError:
        return None
    return f"#{s.upper()}"


def _mix_hex(a, b, ratio):
    a = _normalize_hex(a)
    b = _normalize_hex(b)
    if not a:
        return b or "#3B82F6"
    if not b:
        return a
    ratio = max(0.0, min(1.0, float(ratio)))

    ar, ag, ab = int(a[1:3], 16), int(a[3:5], 16), int(a[5:7], 16)
    br, bg, bb = int(b[1:3], 16), int(b[3:5], 16), int(b[5:7], 16)

    r = round(ar + (br - ar) * ratio)
    g = round(ag + (bg - ag) * ratio)
    bch = round(ab + (bb - ab) * ratio)
    return f"#{r:02X}{g:02X}{bch:02X}"


def get_primary_button_styles(theme_dict, dark_hint=None):
    if not isinstance(theme_dict, dict):
        theme_dict = {}

    explicit_bg = theme_dict.get("primary_gradient")
    explicit_hover = theme_dict.get("primary_gradient_hover")
    if explicit_bg:
        return explicit_bg, explicit_hover or explicit_bg

    primary = _normalize_hex(theme_dict.get("primary", "#3B82F6")) or "#3B82F6"
    if dark_hint is None:
        dark_hint = bool(theme_dict.get("is_dark", False))

    if dark_hint:
        end = _mix_hex(primary, "#FFFFFF", 0.22)
        hover_start = _mix_hex(primary, "#000000", 0.08)
        hover_end = _mix_hex(end, "#FFFFFF", 0.10)
    else:
        end = _mix_hex(primary, "#0F172A", 0.18)
        hover_start = _mix_hex(primary, "#0F172A", 0.10)
        hover_end = _mix_hex(end, "#0F172A", 0.06)

    bg = (
        "qlineargradient(x1:0, y1:0, x2:1, y2:0, "
        f"stop:0 {primary}, stop:1 {end})"
    )
    hover = (
        "qlineargradient(x1:0, y1:0, x2:1, y2:0, "
        f"stop:0 {hover_start}, stop:1 {hover_end})"
    )
    return bg, hover


def resolve_theme_key(mode):
    if not isinstance(mode, str):
        return "light"
    canonical = LEGACY_THEME_MAP.get(mode, mode)
    return canonical if canonical in ZEN_THEME else "light"


def is_dark_theme(mode):
    key = resolve_theme_key(mode)
    c = ZEN_THEME.get(key, ZEN_THEME["light"])
    if "is_dark" in c:
        return bool(c["is_dark"])

    bg = c.get("background", "#FFFFFF")
    if isinstance(bg, str) and bg.startswith("#") and len(bg) >= 7:
        try:
            r = int(bg[1:3], 16)
            g = int(bg[3:5], 16)
            b = int(bg[5:7], 16)
            luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
            return luminance < 140
        except Exception:
            pass

    fg = c.get("foreground", "#000000")
    if isinstance(fg, str) and fg.startswith("#") and len(fg) >= 7:
        try:
            r = int(fg[1:3], 16)
            g = int(fg[3:5], 16)
            b = int(fg[5:7], 16)
            luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
            return luminance > 140
        except Exception:
            pass
    return False


def theme_cycle_order(include_custom=False):
    order = [k for k in CURATED_THEME_ORDER if k in ZEN_THEME]
    if include_custom:
        custom_keys = [k for k in ZEN_THEME if k.startswith("custom_")]
        custom_keys.sort(key=lambda k: ZEN_THEME.get(k, {}).get("display_name", k).lower())
        order.extend(custom_keys)
        if "custom" in ZEN_THEME and "custom" not in order:
            order.append("custom")
    return order


# Compatibility Alias
SHADCN_ZINC = ZEN_THEME

def get_stylesheet(mode="light"):
    mode = resolve_theme_key(mode)
    c = ZEN_THEME.get(mode, ZEN_THEME["light"])
    window_bg = c.get("window_gradient", c["background"])
    sidebar_bg = c.get("sidebar_gradient", c["sidebar_bg"])
    card_bg = c.get("card_gradient", c["card"])
    primary_btn_bg, primary_btn_hover_bg = get_primary_button_styles(
        c, dark_hint=is_dark_theme(mode)
    )
    
    # Common radius and font settings
    radius = "10px" # Refined rounded styling
    
    # Premium Typography System (Neutral & Professional)
    # 1. Inter: engineered for screens, neutral and efficient (ChatGPT Style).
    font = 'font-family: "Inter", "Segoe UI", sans-serif;'
    # 2. Playfair Display: luxury serif for branding.
    display_font = 'font-family: "Playfair Display", serif;'
    # 3. IBM Plex Mono: technical precision.
    mono_font = 'font-family: "IBM Plex Mono", "JetBrains Mono", monospace;'
    
    return f"""
        /* GLOBAL RESET & TYPOGRAPHY */
        * {{
            {font}
            outline: none;
        }}
        
        QMainWindow, QWidget#MainContainer {{
            background: {window_bg};
            color: {c['foreground']};
        }}
        QDialog {{
            background-color: {c['background']};
            color: {c['foreground']};
        }}

        /* --- SIDEBAR --- */
        QWidget#Sidebar {{
            background: {sidebar_bg};
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
            padding: 2px 4px;
            selection-background-color: transparent;
            selection-color: {c['sidebar_fg']};
            outline: none;
        }}
        QTreeWidget::item {{
            padding: 0px;
            border-radius: 10px;
            margin: 1px 4px;
            color: {c['sidebar_fg']};
            font-family: "DM Sans", "Inter", sans-serif;
            font-size: 13px;
        }}
        QTreeWidget::item:hover {{
            background-color: transparent;
        }}
        QTreeWidget::item:selected {{
            background-color: transparent;
            color: {c['sidebar_fg']};
        }}
        
        /* Hide default branch selection highlights (Blue Block fix) */
        QTreeWidget::branch:selected, QTreeWidget::branch:hover {{
            background: transparent;
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
            background: {card_bg};
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
            padding: 0px; /* Controlled via setViewportMargins in editor.py */
            selection-background-color: {c.get('selection_bg', c['secondary'])};
            selection-color: {c.get('selection_fg', c['secondary_foreground'])};
            line-height: 1.2; /* Tighter, more standard line height */
        }}

        QFrame#MetadataBar {{
            background-color: {c['muted']};
            border-top: 1px solid {c['border']};
            border-bottom-left-radius: {radius};
            border-bottom-right-radius: {radius};
            color: {c['muted_foreground']};
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
            background: {primary_btn_bg};
            color: {c['primary_foreground']};
            border: 1px solid {c['primary']};
            border-radius: 10px;
        }}
        QPushButton#PrimaryBtn:hover, QPushButton#NewNoteBtn:hover, QPushButton#NewFolderBtn:hover {{
            background: {primary_btn_hover_bg};
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
            border-radius: 10px; /* Rounded Box Interaction */
            padding: 4px;
        }}
        QPushButton#ViewToggleBtn:hover {{
            background-color: {c['elevated']};
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
            background: transparent;
            width: 6px;
            margin: 2px;
            border-radius: 3px;
        }}
        QScrollBar::handle:vertical {{
            background: {c['scrollbar_handle']};
            min-height: 24px;
            border-radius: 3px;
            margin: 0px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {c.get('muted_foreground', c['scrollbar_handle'])};
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

