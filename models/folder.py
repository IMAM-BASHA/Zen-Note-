import uuid
from models.note import Note
from datetime import datetime

class Folder:
    def __init__(self, name="New Folder", folder_id=None, notes=None, is_pinned=False, is_archived=False, priority=0, created_at=None, color=None, is_locked=False, order=0, cover_image=None, description=None, view_mode="list",
                 trash_original_notebook_id=None, trash_original_notebook_name=None, page_size="free", editor_background_color=None):
        self.id = folder_id if folder_id else str(uuid.uuid4())
        self.name = name
        self.notes = notes if notes else []
        self.is_pinned = is_pinned
        self.is_archived = is_archived
        self.priority = priority # 0=None, 1=High, 2=Med, 3=Low (or user defined)
        # Use ISO format with microseconds for precise sorting (same as Note model)
        self.created_at = created_at if created_at else datetime.now().isoformat(timespec='microseconds')
        self.color = color
        self.is_locked = is_locked
        self.order = order
        self.cover_image = cover_image
        self.description = description
        self.view_mode = view_mode # "list" or "grid"
        self.trash_original_notebook_id = trash_original_notebook_id
        self.trash_original_notebook_name = trash_original_notebook_name
        self.page_size = page_size
        self.editor_background_color = editor_background_color

    def add_note(self, note: Note):
        self.notes.append(note)

    def remove_note(self, note_id):
        self.notes = [n for n in self.notes if n.id != note_id]

    def get_note_by_id(self, note_id):
        for note in self.notes:
            if note.id == note_id:
                return note
        return None

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "is_pinned": self.is_pinned,
            "is_archived": self.is_archived,
            "priority": self.priority,
            "created_at": self.created_at,
            "color": self.color,
            "is_locked": self.is_locked,
            "is_locked": self.is_locked,
            "order": self.order,
            "cover_image": self.cover_image,
            "description": self.description,
            "view_mode": self.view_mode,
            "trash_original_notebook_name": self.trash_original_notebook_name,
            "page_size": getattr(self, 'page_size', 'free'),
            "editor_background_color": getattr(self, 'editor_background_color', None),
            "notes": [note.to_dict() for note in self.notes]
        }

    @classmethod
    def from_dict(cls, data):
        folder = cls(
            folder_id=data.get("id"),
            name=data.get("name", "Untitled Folder"),
            is_pinned=data.get("is_pinned", False),
            is_archived=data.get("is_archived", False),
            priority=data.get("priority", 0),
            created_at=data.get("created_at"),
            color=data.get("color"),
            is_locked=data.get("is_locked", False),
            order=data.get("order", 0),
            cover_image=data.get("cover_image"),
            description=data.get("description"),
            view_mode=data.get("view_mode", "list"),
            trash_original_notebook_id=data.get("trash_original_notebook_id"),
            trash_original_notebook_name=data.get("trash_original_notebook_name"),
            page_size=data.get("page_size", "free"),
            editor_background_color=data.get("editor_background_color"),
            notes=[Note.from_dict(n) for n in data.get("notes", [])]
        )
        return folder

