import os
import shutil
import json
import unittest
import sys
import time
from pathlib import Path

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from storage.data_manager import DataManager, TRASH_DIR
from config import NOTES_DIR

class TestRecursiveDeletion(unittest.TestCase):
    def setUp(self):
        self.dm = DataManager()
        self.test_folder_id = "test_recursive_folder"
        self.test_folder_path = os.path.join(NOTES_DIR, self.test_folder_id)
        
        # Cleanup any previous test data
        if os.path.exists(self.test_folder_path):
            shutil.rmtree(self.test_folder_path)
            
        # Create a test folder and a note
        os.makedirs(self.test_folder_path, exist_ok=True)
        self.note_id = "test_note_1"
        self.note_path = os.path.join(self.test_folder_path, f"{self.note_id}.json")
        with open(self.note_path, 'w', encoding='utf-8') as f:
            json.dump({"id": self.note_id, "title": "Test Note", "content": "Hello"}, f)
            
        # Create a "manual" subfolder to test physical recursion
        self.subfolder_path = os.path.join(self.test_folder_path, "subfolder")
        os.makedirs(self.subfolder_path, exist_ok=True)
        with open(os.path.join(self.subfolder_path, "subnote.json"), 'w', encoding='utf-8') as f:
            json.dump({"id": "sub_note", "title": "Sub Note"}, f)
            
        # Add metadata to settings
        folders_meta = self.dm.get_setting("folders_meta", {})
        folders_meta[self.test_folder_id] = {"color": "red", "last_note_id": self.note_id}
        folders_meta[f"{self.test_folder_id}/subfolder"] = {"color": "blue"}
        self.dm.set_setting("folders_meta", folders_meta)
        
        # Refresh DataManager state
        self.dm.load_data()

    def tearDown(self):
        # Final cleanup
        if os.path.exists(self.test_folder_path):
            shutil.rmtree(self.test_folder_path)
        
        # Clean up trash entries for this folder
        self.dm._purge_trash_for_folder(self.test_folder_id)

    def test_soft_delete_recursive(self):
        print("\nTesting Soft Delete (Move to Trash)...")
        # Ensure it's in folders list
        folder = next((f for f in self.dm.folders if f.id == self.test_folder_id), None)
        self.assertIsNotNone(folder)
        
        # Perform soft delete
        self.dm.delete_folder(self.test_folder_id, permanent=False)
        
        # 1. Verify filesystem movement
        self.assertFalse(os.path.exists(self.test_folder_path))
        
        # Find it in trash
        trash_items = [d for d in os.listdir(TRASH_DIR) if d.startswith(self.test_folder_id)]
        self.assertTrue(len(trash_items) > 0)
        trash_path = os.path.join(TRASH_DIR, trash_items[0])
        
        # Verify subfolders are in trash too
        self.assertTrue(os.path.exists(os.path.join(trash_path, "subfolder")))
        self.assertTrue(os.path.exists(os.path.join(trash_path, "subfolder", "subnote.json")))
        
        # 2. Verify settings metadata is NOT cleaned up yet (it's in Trash, might be restored)
        # Actually, my implementation cleans it up in permanent delete. 
        # In soft delete, we keep it? 
        # Wait, if we keep it, it might conflict if we create a new folder with same name.
        # But restoration needs it. 
        # Actually, restoration should probably pull from .trash_meta.json or similar.
        # My current implementation cleans it up in PERMANENT delete.
        
        folders_meta = self.dm.get_setting("folders_meta", {})
        self.assertIn(self.test_folder_id, folders_meta)
        print("  Soft delete verified: Physical data moved to trash, metadata preserved for restoration.")

    def test_permanent_delete_recursive(self):
        print("\nTesting Permanent Delete...")
        
        # Perform permanent delete
        self.dm.delete_folder(self.test_folder_id, permanent=True)
        
        # 1. Verify filesystem removal
        self.assertFalse(os.path.exists(self.test_folder_path))
        
        # 2. Verify metadata cleanup
        folders_meta = self.dm.get_setting("folders_meta", {})
        self.assertNotIn(self.test_folder_id, folders_meta)
        self.assertNotIn(f"{self.test_folder_id}/subfolder", folders_meta)
        
        print("  Permanent delete verified: Physical data and metadata completely removed.")

    def test_permanent_delete_from_trash(self):
        print("\nTesting Permanent Delete from Trash...")
        
        # Move to trash first
        self.dm.delete_folder(self.test_folder_id, permanent=False)
        trash_items = [d for d in os.listdir(TRASH_DIR) if d.startswith(self.test_folder_id)]
        trash_path = os.path.join(TRASH_DIR, trash_items[0])
        
        # Perform permanent delete of the trash item
        self.dm.permanent_delete_item(trash_path)
        
        # 1. Verify filesystem removal
        self.assertFalse(os.path.exists(trash_path))
        
        # 2. Verify metadata cleanup (handled by permanent_delete_item expansion)
        folders_meta = self.dm.get_setting("folders_meta", {})
        self.assertNotIn(self.test_folder_id, folders_meta)
        
        print("  Permanent delete from trash verified: Metadata cleaned up via .trash_meta.json.")

if __name__ == '__main__':
    unittest.main()
