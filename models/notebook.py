import uuid

class Notebook:
    def __init__(self, name="My Notebook", notebook_id=None, folder_ids=None, is_expanded=True):
        self.id = notebook_id if notebook_id else str(uuid.uuid4())
        self.name = name
        self.folder_ids = folder_ids if folder_ids else []
        self.is_expanded = is_expanded

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "folder_ids": self.folder_ids,
            "is_expanded": self.is_expanded
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            notebook_id=data.get("id"),
            name=data.get("name", "Untitled Notebook"),
            folder_ids=data.get("folder_ids", []),
            is_expanded=data.get("is_expanded", True)
        )
