
import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QListWidget, QTextEdit
from PyQt6.QtCore import Qt

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import ui.styles as styles
from ui.sidebar import Sidebar
from ui.note_list import NoteList
from ui.editor import TextEditor

def verify_theme_logic():
    """Verify that ZEN_THEME is correctly defined and used."""
    print("[-] Verifying ZEN_THEME definition...")
    
    if not hasattr(styles, 'ZEN_THEME'):
        print("[FAIL] ZEN_THEME not found in ui.styles")
        return False
        
    theme = styles.ZEN_THEME
    if "light" not in theme or "dark" not in theme:
        print("[FAIL] ZEN_THEME missing 'light' or 'dark' keys")
        return False
        
    # Check Key Colors (Zen Clarity & Creative Amber)
    light = theme["light"]
    dark = theme["dark"]
    
    expected_light_primary = "#7B9E87" # Sage Green
    expected_dark_primary = "#D97706"  # Amber
    
    if light.get("primary").upper() != expected_light_primary:
        print(f"[WARN] Light primary color mismatch. Expected {expected_light_primary}, got {light.get('primary')}")
    else:
        print("[PASS] Light primary color verified.")
        
    if dark.get("primary").upper() != expected_dark_primary:
        print(f"[WARN] Dark primary color mismatch. Expected {expected_dark_primary}, got {dark.get('primary')}")
    else:
        print("[PASS] Dark primary color verified.")

    print("[-] Verifying Stylesheet Generation...")
    light_css = styles.get_stylesheet("light")
    dark_css = styles.get_stylesheet("dark")
    
    if "Playfair Display" not in light_css:
         print("[FAIL] 'Playfair Display' font missing from stylesheet")
         return False
         
    if "border-radius: 12px" not in light_css:
         print("[WARN] Global border-radius 12px might be missing or different.")
    
    print("[PASS] Stylesheet generation seems correct.")
    return True

def visual_smoke_test():
    """Launch a minimal UI to visually confirm theme application."""
    print("[-] Launching Visual Smoke Test (Close window to finish)...")
    app = QApplication(sys.argv)
    
    window = QMainWindow()
    window.setWindowTitle("Zen Notes Theme Verification")
    window.resize(800, 600)
    
    # Apply Dark Theme initially
    window.setStyleSheet(styles.get_stylesheet("dark"))
    
    label = QLabel("Zen Notes Theme Test - Dark Mode", window)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    window.setCentralWidget(label)
    
    window.show()
    app.exec()
    print("[-] Visual Smoke Test Completed.")

if __name__ == "__main__":
    print("=== Zen Notes Theme Verification ===")
    if verify_theme_logic():
        print("=== Logic Verification Passed ===")
        # visual_smoke_test() # Uncomment to run visual test
    else:
        print("=== Verification FAILED ===")
