import json
import os
import shutil
import re
import tempfile
import time
from glob import glob
from models.folder import Folder
from models.note import Note
from models.notebook import Notebook
from config import DATA_FILE, NOTES_DIR
from util.logger import logger

TRASH_DIR = os.path.join(NOTES_DIR, ".trash")

class DataManager:
    def __init__(self):
        self.folders = []
        self.notebooks = []
        self.settings = {
            "theme_mode": "light",
            "whiteboard_split_view": False,
            "notebooks": [] # List of notebook dicts
        }
        self._ensure_storage()
        self._migrate_if_needed()
        self.load_settings() # Load settings first (meta, theme, notebooks)
        self.load_data()     # Then load data (applying meta)
        self._sync_notebooks() # Ensure all folders are in a notebook

    def get_recent_notes(self, limit=50):
        """Return all notes across all folders, sorted by most recently modified (or created)."""
        all_notes = []
        for folder in self.folders:
            # Skip archived folders? Maybe include them but mark them?
            # For now, include everything that isn't explicitly in trash (folders are active/archived)
            for note in folder.notes:
                # Attach parent folder reference for context (runtime only)
                note._parent_folder = folder
                all_notes.append(note)
            
        # Sort by last match of date. Currently only created_at is strictly tracked on Note.
        # Ideally we'd have modified_at. using created_at for now as proxy or if available.
        # If created_at is string, strict sort might be tricky if formats vary, but ISO is sortable.
        all_notes.sort(key=lambda n: n.created_at, reverse=True)
        return all_notes[:limit]

    def get_trash_notes(self):
        """Parse items from .trash directory (Notes and Folders)."""
        trash_items = []
        if not os.path.exists(TRASH_DIR):
            return []
            
        # 1. Individual Note Files (.json)
        note_files = glob(os.path.join(TRASH_DIR, "*.json"))
        for f_path in note_files:
            try:
                with open(f_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    note = Note.from_dict(data)
                    # Attach path for operations
                    note._trash_path = f_path
                    trash_items.append(note)
            except Exception as e:
                logger.error(f"Failed to load trash note {f_path}: {e}")

        # 2. Trashed Folders (Directories)
        for entry in os.scandir(TRASH_DIR):
            if entry.is_dir():
                meta_path = os.path.join(entry.path, ".trash_meta.json")
                if os.path.exists(meta_path):
                    try:
                        with open(meta_path, 'r', encoding='utf-8') as f:
                            mdata = json.load(f)
                            # Create a dummy note to represent the folder in the list
                            pseudo_note = Note(
                                title=f"Folder: {mdata.get('name', 'Untitled')}",
                                description=f"Contains folder and all its notes.",
                                note_id=mdata.get('id'),
                                trash_original_folder_name=mdata.get('orig_nb_name', 'Notebook')
                            )
                            pseudo_note._is_trash_folder = True
                            pseudo_note._trash_path = entry.path
                            trash_items.append(pseudo_note)
                    except Exception as e:
                        logger.error(f"Failed to load trash folder meta {meta_path}: {e}")
                
        # Sort by creation logic (or we could use ctime for deletion date)
        trash_items.sort(key=lambda n: n.created_at, reverse=True) 
        return trash_items

    def restore_note(self, note_id, trash_path):
        """Restore a single note to its original folder."""
        if not os.path.exists(trash_path): return False
        try:
            with open(trash_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                note = Note.from_dict(data)
            
            orig_folder_name = note.trash_original_folder_name or "Personal"
            target_folder_dir = os.path.join(NOTES_DIR, self._sanitize(orig_folder_name))
            os.makedirs(target_folder_dir, exist_ok=True)
            
            target_path = os.path.join(target_folder_dir, f"{note.id}.json")
            
            # Clean trash metadata before restoring
            note.trash_original_folder_id = None
            note.trash_original_folder_name = None
            with open(trash_path, 'w', encoding='utf-8') as f:
                json.dump(note.to_dict(), f, indent=4)
                
            shutil.move(trash_path, target_path)
            
            # Re-sync in memory
            self.load_data()
            return True
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False

    def restore_folder(self, trash_path):
        """Restore an entire folder and its notebook assignment."""
        if not os.path.exists(trash_path): return False
        try:
            meta_path = os.path.join(trash_path, ".trash_meta.json")
            with open(meta_path, 'r', encoding='utf-8') as f:
                mdata = json.load(f)
            
            orig_id = mdata.get('id')
            target_path = os.path.join(NOTES_DIR, self._sanitize(orig_id))
            
            # Remove meta file before moving back
            os.remove(meta_path)
            shutil.move(trash_path, target_path)
            
            # Restore notebook mapping if possible
            orig_nb_id = mdata.get('orig_nb_id')
            if orig_nb_id:
                nb = next((n for n in self.notebooks if n.id == orig_nb_id), None)
                if nb and orig_id not in nb.folder_ids:
                    nb.folder_ids.append(orig_id)
                    self.save_settings()
            
            self.load_data()
            return True
        except Exception as e:
            logger.error(f"Folder restore failed: {e}")
            return False

    def permanent_delete_item(self, trash_path):
        """Permanently remove item from disk."""
        if not os.path.exists(trash_path): return
        try:
            if os.path.isdir(trash_path):
                shutil.rmtree(trash_path)
            else:
                os.remove(trash_path)
        except Exception as e:
            logger.error(f"Permanent delete failed: {e}")

    def empty_trash(self):
        """Delete everything in the .trash directory."""
        if os.path.exists(TRASH_DIR):
            try:
                # Instead of removing TRASH_DIR, we remove its contents to keep the dir
                for entry in os.scandir(TRASH_DIR):
                    if entry.is_dir():
                        shutil.rmtree(entry.path)
                    else:
                        os.remove(entry.path)
                return True
            except Exception as e:
                logger.error(f"Empty trash failed: {e}")
        return False

    def _ensure_storage(self):
        os.makedirs(NOTES_DIR, exist_ok=True)
        os.makedirs(TRASH_DIR, exist_ok=True)

    def _safe_save_json(self, file_path, data):
        """Atomic write using temporary file and rename."""
        temp_fd, temp_path = tempfile.mkstemp(dir=os.path.dirname(file_path), suffix=".tmp")
        try:
            with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            # Ensure data is flushed to disk
            os.replace(temp_path, file_path)
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise e

    def _sanitize(self, name):
        """Sanitize string to be safe for filenames."""
        s = str(name).strip()
        # Block directory traversal
        if ".." in s:
            s = s.replace("..", "__")
        # Remove control characters
        s = "".join(c for c in s if c.isprintable())
        # Replace illegal filename characters
        return re.sub(r'[<>:"/\\|?*]', '_', s).strip()

    def _migrate_if_needed(self):
        """Migrate legacy data.json to filesystem structure."""
        if os.path.exists(DATA_FILE) and not os.listdir(NOTES_DIR):
            logger.info("Migrating data.json to Filesystem...")
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for folder_data in data:
                    f_name = self._sanitize(folder_data.get('name', 'Untitled'))
                    f_path = os.path.join(NOTES_DIR, f_name)
                    os.makedirs(f_path, exist_ok=True)
                    
                    folder_obj = Folder.from_dict(folder_data)
                    for note in folder_obj.notes:
                        # Use UUID as filename for robustness
                        n_path = os.path.join(f_path, f"{note.id}.json")
                        with open(n_path, 'w', encoding='utf-8') as nf:
                            json.dump(note.to_dict(), nf, indent=4)
                
                # Backup original file
                try:
                    os.rename(DATA_FILE, DATA_FILE + ".bak")
                except OSError as e:
                    logger.warning(f"Could not backup data file: {e}")
            except Exception as e:
                logger.error(f"Migration failed", exc_info=True)

    def load_data(self):
        """Load folders and notes from filesystem with optimizations."""
        self.folders = []
        if not os.path.exists(NOTES_DIR): return
        
        # Scan directories (Folders)
        for entry in os.scandir(NOTES_DIR):
            if entry.is_dir():
                folder_name = entry.name
                
                # Ignore hidden folders (like .trash)
                if folder_name.startswith('.'):
                    continue

                # Use folder name as ID for now to align with FS
                folder = Folder(name=folder_name, folder_id=folder_name)
                
                # Scan JSON files (Notes)
                notes = []
                json_files = glob(os.path.join(entry.path, "*.json"))
                
                garbage_files = []
                
                # Batch load notes with error handling
                for jf in json_files:
                    # Fix: Skip whiteboard files from being treated as notes
                    if os.path.basename(jf).startswith("whiteboard"):
                        continue
                        
                    try:
                        with open(jf, 'r', encoding='utf-8') as f:
                            ndata = json.load(f)
                            note = Note.from_dict(ndata)
                            
                            # CLEANUP: Check for empty notes
                            # Robust Logic: Check for real text OR significant HTML elements (images, tables)
                            has_content = False
                            
                            # 1. Text Check (strip tags) - Optimized with Length Heuristic
                            # Avoid running regex on large notes (slow). If > 1000 chars, assume valid.
                            if len(note.content) > 1000:
                                has_content = True
                            else:
                                raw_text = re.sub(r'<[^>]+>', '', note.content).strip()
                                if raw_text:
                                    has_content = True
                                
                            # 2. Structure Check (images, diagrams, tables)
                            if not has_content:
                                if "<img" in note.content or "<table" in note.content:
                                    has_content = True

                            # Check titles
                            is_empty_title = note.title in ["New Note", "Untitled", ""] or not note.title.strip()
                            
                            # If no content AND default title -> Garbage
                            if is_empty_title and not has_content:
                                garbage_files.append(jf)
                            else:
                                notes.append(note)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to decode note {jf}: {e}")
                    except Exception as e:
                        logger.error(f"Failed to load note {jf}: {e}")

                # Delete garbage files
                for gjf in garbage_files:
                    try:
                        logger.info(f"Deleting empty temporary note: {gjf}")
                        os.remove(gjf)
                    except Exception as e:
                        logger.error(f"Failed to delete {gjf}: {e}")

                # Only process notes if there are any
                if notes:
                    # Check if any notes need migration (missing or None order) - Optimized with list comprehension
                    notes_need_order = [n for n in notes if not hasattr(n, 'order') or n.order is None]
                    
                    if notes_need_order:
                        # Sort all notes by creation date for initial ordering
                        notes.sort(key=lambda x: x.created_at or "")
                        # Assign sequential order to ALL notes
                        for idx, note in enumerate(notes):
                            note.order = idx
                            # Save the note with order
                            self.save_note(folder, note)
                    
                    # Always sort by order field for display
                    notes.sort(key=lambda x: (x.order if x.order is not None else 999999))
                
                folder.notes = notes
                
                # Apply Metadata from Settings (Pin, Priority)
                # Settings structure: {"folders_meta": { "folder_id": {"is_pinned": bool, "priority": int} }}
                folders_meta = self.get_setting("folders_meta", {})
                if folder.id in folders_meta:
                    meta = folders_meta[folder.id]
                    folder.is_pinned = meta.get("is_pinned", False)
                    folder.is_archived = meta.get("is_archived", False)
                    folder.priority = meta.get("priority", 0)
                    folder.color = meta.get("color", None)
                    folder.is_locked = meta.get("is_locked", False)
                
                self.folders.append(folder)

    def update_folder_last_note(self, folder_id, note_id):
        """Update the last opened note ID for a folder."""
        folders_meta = self.get_setting("folders_meta", {})
        if folder_id not in folders_meta:
            folders_meta[folder_id] = {}
        
        folders_meta[folder_id]["last_note_id"] = note_id
        self.set_setting("folders_meta", folders_meta)
        self.save_settings()

    def save_note(self, folder, note):
        """Save a single note to disk with atomic write and robust error handling."""
        if not folder or not note: return
        
        try:
            f_path = os.path.join(NOTES_DIR, self._sanitize(folder.name))
            os.makedirs(f_path, exist_ok=True)
            
            # We use Note UUID as filename to allow title renaming without file renaming issues
            n_path = os.path.join(f_path, f"{note.id}.json")
            self._safe_save_json(n_path, note.to_dict())
        except (IOError, OSError, PermissionError) as e:
            logger.error(f"Error saving note {note.id}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error saving note {note.id}", exc_info=True)

    def add_folder(self, name):
        """Create a new folder directory."""
        safe_name = self._sanitize(name)
        # Avoid duplicates
        if any(f.name == safe_name for f in self.folders):
            safe_name += "_" + str(len(self.folders))
            
        path = os.path.join(NOTES_DIR, safe_name)
        os.makedirs(path, exist_ok=True)
        
        folder = Folder(name=safe_name, folder_id=safe_name)
        self.folders.append(folder)
        return folder

    def delete_folder(self, folder_id, permanent=False):
        """Delete folder, either moving to trash (default) or permanently."""
        # Prevent deleting the trash directory itself or hidden folders
        if folder_id.startswith('.') or "trash" in folder_id.lower():
             logger.warning(f"Attempted to delete protected folder: {folder_id}")
             return

        folder = next((f for f in self.folders if f.id == folder_id), None)
        if not folder: return

        path = os.path.join(NOTES_DIR, self._sanitize(folder_id))
        
        if permanent:
            if os.path.exists(path):
                try:
                    shutil.rmtree(path)
                    print(f"Folder '{folder_id}' permanently deleted.")
                except Exception as e:
                    logger.error(f"Permanent folder delete failed: {e}")
            
            # Surgically purge any items in the .trash that belonged to this folder
            self._purge_trash_for_folder(folder_id)

            # Cleanup metadata in settings
            folders_meta = self.get_setting("folders_meta", {})
            if folder_id in folders_meta:
                del folders_meta[folder_id]
                self.set_setting("folders_meta", folders_meta)
        else:
            # Find original notebook for restoration context
            orig_nb = None
            for nb in self.notebooks:
                if folder_id in nb.folder_ids:
                    orig_nb = nb
                    break

            folder.trash_original_notebook_id = orig_nb.id if orig_nb else None
            folder.trash_original_notebook_name = orig_nb.name if orig_nb else "Personal Notebook"

            if os.path.exists(path):
                try:
                    # Move to trash with unique name to avoid collisions
                    trash_name = f"{self._sanitize(folder_id)}_{int(time.time())}"
                    trash_path = os.path.join(TRASH_DIR, trash_name)
                    
                    # Save metadata file inside the trashed folder for restoration
                    meta_path = os.path.join(path, ".trash_meta.json")
                    with open(meta_path, 'w', encoding='utf-8') as f:
                        json.dump({
                            "id": folder.id,
                            "name": folder.name,
                            "orig_nb_id": folder.trash_original_notebook_id,
                            "orig_nb_name": folder.trash_original_notebook_name,
                            "type": "folder"
                        }, f)

                    shutil.move(path, trash_path)
                    print(f"Folder '{folder_id}' moved to trash: {trash_path}")
                except Exception as e:
                    print(f"Soft delete failed, fallback to permanent deletion: {e}")
                    shutil.rmtree(path)
                    
        self.folders = [f for f in self.folders if f.id != folder_id]

    def delete_note(self, folder, note_id):
        """Move note file to trash (Soft Delete)."""
        if not folder: return
        note = folder.get_note_by_id(note_id)
        if not note: return

        # Set metadata for restoration
        note.trash_original_folder_id = folder.id
        note.trash_original_folder_name = folder.name
        
        folder.remove_note(note_id)
        
        target_note_path = os.path.join(NOTES_DIR, self._sanitize(folder.name), f"{note_id}.json")
        if os.path.exists(target_note_path):
            try:
                # Save metadata in the JSON before moving
                with open(target_note_path, 'w', encoding='utf-8') as f:
                    json.dump(note.to_dict(), f, indent=4)

                trash_note_path = os.path.join(TRASH_DIR, f"{note_id}_{int(time.time())}.json")
                shutil.move(target_note_path, trash_note_path)
            except Exception as e:
                print(f"Soft delete failed for note, fallback to permanent: {e}")
                os.remove(target_note_path)
    
    def move_note_between_folders(self, note_id, source_folder, target_folder):
        """Move a note from source folder to target folder."""
        if not source_folder or not target_folder:
            return False
        
        if source_folder.id == target_folder.id:
            return False  # Cannot move to same folder
        
        # Find the note in source folder
        note = next((n for n in source_folder.notes if n.id == note_id), None)
        if not note:
            return False
        
        # Get paths
        source_path = os.path.join(NOTES_DIR, self._sanitize(source_folder.name), f"{note_id}.json")
        target_dir = os.path.join(NOTES_DIR, self._sanitize(target_folder.name))
        target_path = os.path.join(target_dir, f"{note_id}.json")
        
        # Ensure target directory exists
        os.makedirs(target_dir, exist_ok=True)
        
        # Move the note file
        try:
            if os.path.exists(source_path):
                shutil.move(source_path, target_path)
            
            # Update folder structures
            source_folder.remove_note(note_id)
            target_folder.add_note(note)
            note.order = len(target_folder.notes) - 1  # Add to end of target folder
            
            # Normalize order in both folders
            self._normalize_note_order(source_folder)
            self._normalize_note_order(target_folder)
            
            return True
        except Exception as e:
            print(f"Error moving note {note_id}: {e}")
            return False
    
    def get_folder_by_id(self, folder_id):
        for folder in self.folders:
            if folder.id == folder_id:
                return folder
        return None
        
    def get_folder_path(self, folder):
        """Get absolute filesystem path for a folder."""
        if not folder: return None
        return os.path.join(NOTES_DIR, self._sanitize(folder.name))

    def rename_folder(self, folder_id, new_name):
        """Rename a folder (directory and internal data)."""
        folder = self.get_folder_by_id(folder_id)
        if not folder:
            return False
        
        old_name = folder.name
        safe_new_name = self._sanitize(new_name)
        
        # Check for duplicates
        if any(f.name == safe_new_name and f.id != folder_id for f in self.folders):
            return False  # Name conflict
        
        old_path = os.path.join(NOTES_DIR, old_name)
        new_path = os.path.join(NOTES_DIR, safe_new_name)
        
        # Rename directory on filesystem
        if os.path.exists(old_path):
            try:
                os.rename(old_path, new_path)
                # Update folder object
                folder.name = safe_new_name
                folder.id = safe_new_name  # Keep ID in sync with folder name
                return True
            except Exception as e:
                print(f"Failed to rename folder: {e}")
                return False
        return False

    def rename_note(self, folder_id, note_id, new_title):
        """Rename a note (update title in file)."""
        folder = self.get_folder_by_id(folder_id)
        if not folder:
            return False
        
        note = next((n for n in folder.notes if n.id == note_id), None)
        if not note:
            return False
        
        # Update note title
        note.title = new_title
        
        # Save the updated note
        self.save_note(folder, note)
        return True

    def _normalize_note_order(self, folder):
        """Helper: ensure all notes have sequential order values (0, 1, 2, ...)."""
        if not folder or not folder.notes:
            return
        
        # Do NOT sort here. We trust the list order is correct (from reorder/insert).
        # Just reassign sequential order based on current list position.
        
        # Reassign sequential order
        for idx, note in enumerate(folder.notes):
            note.order = idx
    
    def reorder_note(self, folder_id, note_id, new_position):
        """Move a note to a new position and renumber others."""
        folder = self.get_folder_by_id(folder_id)
        if not folder or not folder.notes:
            return False
        
        # Find the note
        note = next((n for n in folder.notes if n.id == note_id), None)
        if not note:
            return False
        
        # CRITICAL FIX: Ensure internal list matches UI Sort Order before processing index
        # The UI sorts by (Pinned, Priority, Order). DataManager must match this
        # to ensure the 'new_position' index is applied to the correct sequence.
        folder.notes.sort(key=Note.sort_key)
        
        # Clamp position to valid range
        new_position = max(0, min(new_position, len(folder.notes) - 1))
        
        # Get current position
        current_position = folder.notes.index(note)
        
        # No change needed
        if current_position == new_position:
            return True
        
        # Remove from current position
        folder.notes.pop(current_position)
        
        # Insert at new position
        folder.notes.insert(new_position, note)
        
        # Capture old orders to minimize IO
        old_orders = {n.id: n.order for n in folder.notes}
        
        # Normalize order
        self._normalize_note_order(folder)
        
        # Save ONLY affected notes (Optimization)
        for n in folder.notes:
            if n.order != old_orders.get(n.id):
                self.save_note(folder, n)
        
        return True
    
    def insert_note_at_position(self, folder, note, position):
        """Insert a new note at specific position and shift others down."""
        if not folder:
            return False
        
        # Clamp position to valid range
        position = max(0, min(position, len(folder.notes)))
        
        # Insert at position
        folder.notes.insert(position, note)
        
        # Normalize order
        self._normalize_note_order(folder)
        
        # Save all affected notes
        for n in folder.notes:
            self.save_note(folder, n)
        
        return True

    def save_data(self):
        """Deprecated full save. No-op in FS mode."""
        pass

    def load_settings(self):
        try:
            if os.path.exists("settings.json"):
                with open("settings.json", 'r') as f:
                    self.settings.update(json.load(f))
        except Exception as e:
            print(f"Failed to load settings: {e}")

    def get_setting(self, key, default=None):
        return self.settings.get(key, default)

    # --- Notebook Management ---
    
    def _sync_notebooks(self):
        """Ensure all folders are assigned to a notebook. Create a default if none exist."""
        notebook_data = self.get_setting("notebooks", [])
        self.notebooks = [Notebook.from_dict(d) for d in notebook_data]
        
        # If no notebooks, create a default one
        if not self.notebooks:
            default_nb = self.add_notebook("Personal Notebook")
            # Put all non-archived folders in it
            default_nb.folder_ids = [f.id for f in self.folders if not getattr(f, 'is_archived', False)]
            self.save_settings()
        else:
            # Fix: Ensure every folder belongs to AT LEAST one notebook
            assigned_ids = set()
            for nb in self.notebooks:
                assigned_ids.update(nb.folder_ids)
            
            # Now includes archived folders too
            missing_ids = [f.id for f in self.folders if f.id not in assigned_ids]
            if missing_ids:
                # Add to the first notebook
                self.notebooks[0].folder_ids.extend(missing_ids)
                self.save_settings()

    def add_notebook(self, name):
        nb = Notebook(name=name)
        self.notebooks.append(nb)
        self.save_settings()
        return nb

    def delete_notebook(self, nb_id):
        # Cascaded Deletion: Delete all folders within this notebook PERMANENTLY
        nb = next((n for n in self.notebooks if n.id == nb_id), None)
        if nb:
            # First, pull any member folders already in the trash
            self._purge_trash_for_notebook(nb_id)

            # We copy the list to avoid mutation issues during iteration
            for folder_id in list(nb.folder_ids):
                self.delete_folder(folder_id, permanent=True)

        self.notebooks = [nb for nb in self.notebooks if nb.id != nb_id]
        self.save_settings()

    def _purge_trash_for_folder(self, folder_id):
        """Permanently remove any items in the Trash that belonged to this specific folder."""
        if not os.path.exists(TRASH_DIR): return
        
        # 1. Notes
        for f_path in glob(os.path.join(TRASH_DIR, "*.json")):
            try:
                with open(f_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data.get('trash_original_folder_id') == folder_id:
                        os.remove(f_path)
            except: pass

        # 2. Folders
        for entry in os.scandir(TRASH_DIR):
            if entry.is_dir():
                meta_path = os.path.join(entry.path, ".trash_meta.json")
                if os.path.exists(meta_path):
                    try:
                        with open(meta_path, 'r', encoding='utf-8') as f:
                            mdata = json.load(f)
                            if mdata.get('id') == folder_id:
                                shutil.rmtree(entry.path)
                    except: pass

    def _purge_trash_for_notebook(self, nb_id):
        """Surgically remove any trashed folders that belonged to this notebook."""
        if not os.path.exists(TRASH_DIR): return
        for entry in os.scandir(TRASH_DIR):
            if entry.is_dir():
                meta_path = os.path.join(entry.path, ".trash_meta.json")
                if os.path.exists(meta_path):
                    try:
                        with open(meta_path, 'r', encoding='utf-8') as f:
                            mdata = json.load(f)
                            if mdata.get('orig_nb_id') == nb_id:
                                shutil.rmtree(entry.path)
                    except: pass

    def add_folder_to_notebook(self, folder_id, nb_id):
        """Associate a folder with a specific notebook."""
        nb = next((n for n in self.notebooks if n.id == nb_id), None)
        if nb:
            if folder_id not in nb.folder_ids:
                nb.folder_ids.append(folder_id)
                self.save_settings()
            return True
        return False

    def save_settings(self):
        """Override to persist notebooks objects into dicts."""
        self.settings["notebooks"] = [nb.to_dict() for nb in self.notebooks]
        try:
            self._safe_save_json("settings.json", self.settings)
        except Exception as e:
            print(f"Failed to save settings: {e}")

    def set_setting(self, key, value):
        self.settings[key] = value
        self.save_settings()

