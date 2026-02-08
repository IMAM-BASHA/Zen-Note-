import uuid
from datetime import datetime

class Note:
    def __init__(self, title="New Note", content="", created_at=None, note_id=None, whiteboard_images=None, order=None, is_pinned=False, is_archived=False, priority=0, color=None, is_locked=False, last_scroll_position=0, content_splitter_sizes=None, cover_image=None, description=None, last_opened=None, closed_at=None):
        self.id = note_id if note_id else str(uuid.uuid4())
        self.title = title
        self.content = content  # HTML content
        self.whiteboard_images = whiteboard_images if whiteboard_images else {} # {res_name: b64_data}
        self.created_at = created_at if created_at else datetime.now().isoformat(timespec='microseconds')
        self.order = order if order is not None else 0
        self.is_pinned = is_pinned
        self.is_archived = is_archived
        self.priority = priority # 0=None, 1=High, 2=Med, 3=Low
        self.color = color
        self.is_locked = is_locked
        self.last_scroll_position = last_scroll_position
        self.content_splitter_sizes = content_splitter_sizes # [int, int, int] for nested splitter
        self.cover_image = cover_image
        self.description = description
        self.last_opened = last_opened
        self.closed_at = closed_at

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "whiteboard_images": self.whiteboard_images,
            "created_at": self.created_at,
            "order": self.order,
            "is_pinned": self.is_pinned,
            "is_archived": self.is_archived,
            "priority": self.priority,
            "color": self.color,
            "is_locked": self.is_locked,
            "last_scroll_position": self.last_scroll_position,
            "content_splitter_sizes": self.content_splitter_sizes,
            "cover_image": self.cover_image,
            "description": self.description,
            "last_opened": self.last_opened,
            "closed_at": self.closed_at
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            note_id=data.get("id"),
            title=data.get("title", "Untitled"),
            content=data.get("content", ""),
            whiteboard_images=data.get("whiteboard_images", {}),
            created_at=data.get("created_at"),
            order=data.get("order"),
            is_pinned=data.get("is_pinned", False),
            is_archived=data.get("is_archived", False),
            priority=data.get("priority", 0),
            color=data.get("color", None),
            is_locked=data.get("is_locked", False),
            last_scroll_position=data.get("last_scroll_position", 0),
            content_splitter_sizes=data.get("content_splitter_sizes"),
            cover_image=data.get("cover_image"),
            description=data.get("description"),
            last_opened=data.get("last_opened"),
            closed_at=data.get("closed_at")
        )
    
    @staticmethod
    def sort_key(n):
        """
        Returns a tuple for sorting notes consistently across app.
        Order: Pinned first, then by Priority (1,2,3), then by custom Order.
        """
        pinned_rank = not getattr(n, 'is_pinned', False)  # False (0) comes before True (1)
        p = getattr(n, 'priority', 0)
        priority_rank = p if p > 0 else 999  # 0 = no priority, sort last
        order_rank = getattr(n, 'order', 0)
        return (pinned_rank, priority_rank, order_rank)

