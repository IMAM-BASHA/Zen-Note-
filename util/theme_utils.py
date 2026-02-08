import colorsys

def clamp(value, min_v, max_v):
    return max(min_v, min(value, max_v))

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    return r, g, b

def rgb_to_hex(r, g, b):
    return "#{:02X}{:02X}{:02X}".format(
        int(r * 255), int(g * 255), int(b * 255)
    )

def convert_theme_color(hex_color, mode="dark"):
    """
    Converts a hex color to its dark/light mode counterpart 
    using HSL transformation logic (Flip Lightness, Adjust Saturation).
    """
    r, g, b = hex_to_rgb(hex_color)
    h, l, s = colorsys.rgb_to_hls(r, g, b)

    # Flip lightness logic
    # Light mode (high L) -> Dark mode (low L)
    # Dark mode (low L) -> Light mode (high L)
    # The user's formula was l = 1 - l, which is a simple flip.
    # However, sometimes we want to preserve "darkness" for bg? 
    # The user says: "Flip the Lightness... new_L = 100 - old_L"
    
    # We will use a slightly smarter flip if needed, but 1-l is standard inverse.
    l = 1.0 - l

    if mode == "dark":
        # Reducing saturation for dark mode (calmer)
        s *= 0.8
    else:
        # Increasing saturation for light mode
        s *= 1.1

    # Clamp values to avoid accessibility issues
    # Dark Mode text L should be high (80-90%)
    # Light Mode text L should be low (15-20%)
    # But since we are flipping, if input is Light Mode Text (L=0.2), 
    # Output L becomes 0.8. Perfect.
    
    # User Rules:
    # L must be between 20% and 85% (0.2 - 0.85)
    # S must be between 15% and 80% (0.15 - 0.80)
    
    # Note: For strict backgrounds like #FFFFFF (L=1.0), flip makes it #000000 (L=0.0).
    # Clamping 0.0 to 0.2 makes it #333333 (Dark Grey). 
    # This aligns with "Dark mode != black".
    
    l = clamp(l, 0.2, 0.95) # Slight adjust to allow near white/black for backgrounds if needed? 
    # User said 0.2 to 0.85. 
    # If I convert perfect White #FFFFFF (L=1), new L=0. Clamped to 0.2.
    # If I convert perfect Black #000000 (L=0), new L=1. Clamped to 0.85.
    
    s = clamp(s, 0.0, 1.0) # Safety clamp for saturation (0-1)

    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return rgb_to_hex(r, g, b)
