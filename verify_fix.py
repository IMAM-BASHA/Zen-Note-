
import os
import shutil
import sys
import json

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from storage.data_manager import DataManager
import config

def verify_fix():
    print("Starting verification of folder deletion fix...")
    
    # Use a temp directory for testing
    import tempfile
    with tempfile.TemporaryDirectory() as temp_dir:
        config.NOTES_DIR = temp_dir
        config.DATA_FILE = os.path.join(temp_dir, "data.json")
        
        # We need to monkey-patch the module-level constants in data_manager
        import storage.data_manager
        storage.data_manager.NOTES_DIR = temp_dir
        storage.data_manager.DATA_FILE = config.DATA_FILE
        storage.data_manager.TRASH_DIR = os.path.join(temp_dir, ".trash")
        
        from storage.data_manager import DataManager
        dm = DataManager()
        
        # Test Case 1: Can we delete a folder named "Trash"?
        print(f"Testing Case 1: Delete folder named 'Trash' in {temp_dir}")
        folder_trash = dm.add_folder("Trash")
        assert os.path.exists(os.path.join(temp_dir, "Trash"))
        
        dm.delete_folder("Trash", permanent=True)
        if os.path.exists(os.path.join(temp_dir, "Trash")):
            print("FAILED: Folder 'Trash' still exists after permanent deletion.")
            return False
        else:
            print("PASSED: Folder 'Trash' successfully deleted.")

        # Test Case 2: Is ".trash" still protected?
        print("Testing Case 2: Ensure '.trash' is protected")
        os.makedirs(os.path.join(temp_dir, ".trash"), exist_ok=True)
        dm.delete_folder(".trash", permanent=True)
        if os.path.exists(os.path.join(temp_dir, ".trash")):
            print("PASSED: '.trash' is still protected.")
        else:
            print("FAILED: '.trash' was deleted!")
            return False
            
    print("\nALL VERIFICATION TESTS PASSED!")
    return True

if __name__ == "__main__":
    if verify_fix():
        sys.exit(0)
    else:
        sys.exit(1)
