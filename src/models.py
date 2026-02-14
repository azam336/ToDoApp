"""Data model for a to-do item."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    return str(uuid.uuid4())


@dataclass
class TodoItem:
    title: str
    category: str = "General"
    done: bool = False
    id: str = field(default_factory=_new_id)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    def touch(self) -> None:
        """Refresh updated_at to current time."""
        self.updated_at = _now_iso()

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> TodoItem:
        return cls(**data)
