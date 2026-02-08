from PyQt6.QtGui import QKeySequence
from util.logger import logger

class ShortcutManager:
    """Manages application shortcuts with persistence."""
    
    # Default Shortcut Definitions
    # Format: 'action_id': ('Default Key', 'Description')
    DEFAULTS = {
        # Global
        'global_new_note': ('Ctrl+Alt+N', 'New Note'),
        'global_new_folder': ('Ctrl+Shift+N', 'New Folder'),
        'global_save': ('Ctrl+S', 'Save'),
        
        # Editor - Formatting
        'editor_undo': ('Ctrl+Z', 'Undo'),
        'editor_redo': ('Ctrl+Y', 'Redo'),
        'editor_bold': ('Ctrl+B', 'Bold'),
        'editor_italic': ('Ctrl+I', 'Italic'),
        'editor_underline': ('Ctrl+U', 'Underline'),
        'editor_highlight': ('Ctrl+H', 'Highlighter (Default)'),
        'editor_custom_highlight': ('Ctrl+J', 'Custom Highlighter'),
        'editor_font_inc': ('Ctrl++', 'Increase Font Size'),
        'editor_font_inc': ('Ctrl++', 'Increase Font Size'),
        'editor_font_dec': ('Ctrl+-', 'Decrease Font Size'),
        
        # Editor - Search
        'editor_search': ('Ctrl+F', 'Find in Note'),
        
        # Editor - Insert
        'editor_smart_copy': ('Ctrl+C', 'Smart Copy / Code Block'),
        'editor_insert_note_box': ('Ctrl+N', 'Insert Note Box'),
        'editor_insert_drawing': ('Ctrl+Q', 'Insert Drawing'),
        'editor_import_image': ('Ctrl+Shift+I', 'Import Whiteboard Image'),
        'editor_insert_hr': ('Ctrl+L', 'Insert Horizontal Line'),
        
        # Global - View/Tools
        'global_toggle_theme': ('Ctrl+T', 'Toggle Theme'),
        'global_highlight_preview': ('Ctrl+Shift+H', 'Preview Highlights'),
        'global_pdf_preview': ('Ctrl+Shift+P', 'Preview Folder PDF'),
    }

    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.shortcuts = {}
        self.load_shortcuts()

    def load_shortcuts(self):
        """Load shortcuts from settings, falling back to defaults."""
        saved_shortcuts = self.data_manager.get_setting('shortcuts', {})
        
        self.shortcuts = {}
        for action_id, (default_key, desc) in self.DEFAULTS.items():
            # Use saved key if exists, else default
            self.shortcuts[action_id] = saved_shortcuts.get(action_id, default_key)

    def get_shortcut(self, action_id):
        """Get the key sequence string for an action."""
        return self.shortcuts.get(action_id, "")

    def get_description(self, action_id):
        """Get the description for an action."""
        if action_id in self.DEFAULTS:
            return self.DEFAULTS[action_id][1]
        return "Unknown Action"

    def set_shortcut(self, action_id, key_sequence):
        """Update a shortcut and save."""
        if action_id in self.DEFAULTS:
            self.shortcuts[action_id] = key_sequence
            self._save()

    def reset_to_default(self, action_id):
        """Reset a specific shortcut to default."""
        if action_id in self.DEFAULTS:
            self.shortcuts[action_id] = self.DEFAULTS[action_id][0]
            self._save()
            
    def reset_all(self):
        """Reset all shortcuts to defaults."""
        for action_id, (default_key, _) in self.DEFAULTS.items():
            self.shortcuts[action_id] = default_key
        self._save()

    def _save(self):
        """Persist to DataManager."""
        self.data_manager.set_setting('shortcuts', self.shortcuts)

    def get_action_for_key(self, key_sequence):
        """Find action ID mapped to a specific key sequence."""
        # This is a linear search, but valid for small number of shortcuts
        for action_id, key in self.shortcuts.items():
            if key == key_sequence:
                return action_id
        return None

    def get_all_shortcuts(self):
        """Return dict of {action_id: current_key}."""
        return self.shortcuts.copy()
